"""Own one local Uvicorn process for a notebook or a small teaching example.

This helper supports Linux (including Colab) and macOS. It reserves a loopback
socket and passes its descriptor to Uvicorn, avoiding a free-port selection race.
It neither imports an example application nor loads a .env file.
"""
from __future__ import annotations

import atexit
from collections.abc import Mapping
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ServiceProcess:
    """Start, check and stop only the Uvicorn child created by this object.

    ``env`` adds or replaces application settings; a value of ``None`` removes
    a variable. By default the parent environment is inherited. Pass
    ``inherit_env=False`` to start from an empty environment plus explicit
    settings. This generic helper supplies no application/provider policy.
    Uvicorn environment defaults are always removed to keep one owned process.

    Readiness means this child is alive and its loopback ``health_path`` returns
    ``health_status`` (default 200). Optional ``health_headers`` support protected
    health routes. It does not establish any downstream dependency's readiness.
    ``factory=True`` asks Uvicorn to call the supplied zero-argument app factory.
    Child stdout/stderr are discarded (zero retained log bytes), so exceptions
    never include application output, environment settings or credentials.
    """

    def __init__(
        self,
        app: str = "app.main:app",
        *,
        project_dir: Path,
        port: int = 0,
        env: Mapping[str, str | None] | None = None,
        inherit_env: bool = True,
        startup_timeout: float = 15.0,
        health_path: str = "/health",
        health_status: int = 200,
        health_headers: Mapping[str, str] | None = None,
        factory: bool = False,
    ) -> None:
        if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
            raise ValueError("port must be an integer between 0 and 65535.")
        if startup_timeout <= 0 or not startup_timeout < float("inf"):
            raise ValueError("startup_timeout must be a finite positive number.")
        if not health_path.startswith("/") or any(char in health_path for char in "\r\n?#"):
            raise ValueError("health_path must be an absolute URL path without query or fragment.")
        if not isinstance(inherit_env, bool) or not isinstance(factory, bool):
            raise TypeError("inherit_env and factory must be booleans.")
        if not isinstance(health_status, int) or isinstance(health_status, bool) or not 100 <= health_status <= 599:
            raise ValueError("health_status must be an HTTP status integer between 100 and 599.")
        settings = dict(env or {})
        if any(not isinstance(key, str) or not key or "=" in key or "\0" in key
               or (value is not None and (not isinstance(value, str) or "\0" in value))
               for key, value in settings.items()):
            raise ValueError("env must map valid environment names to strings or None.")
        headers = dict(health_headers or {})
        if any(not isinstance(key, str) or not key or not isinstance(value, str)
               or any(char in key + value for char in "\r\n\0")
               for key, value in headers.items()):
            raise ValueError("health_headers must map header names to strings without control separators.")
        self.app = app
        self.project_dir = Path(project_dir).expanduser().resolve()
        self._requested_port = port
        self._env = settings
        self._inherit_env = inherit_env
        self._factory = factory
        self._startup_timeout = float(startup_timeout)
        self._health_path = health_path
        self._health_status = health_status
        self._health_headers = headers
        self._process: subprocess.Popen | None = None
        self._base_url: str | None = None
        self._atexit_registered = False
        self._lock = threading.RLock()
        # Local health must bypass shell proxies and must not follow redirects.
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    @property
    def base_url(self) -> str | None:
        return self._base_url

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _healthy(self, timeout: float = 0.25) -> bool:
        if not self.is_running or self._base_url is None:
            return False
        try:
            request = Request(self._base_url + self._health_path, method="GET", headers=self._health_headers)
            with self._opener.open(request, timeout=timeout) as response:
                ready = response.status == self._health_status
            return ready and self.is_running
        except HTTPError as response:
            # urllib raises for some statuses even when explicitly expected.
            ready = response.code == self._health_status
            response.close()
            return ready and self.is_running
        except (URLError, OSError, ValueError):
            return False

    def _child_environment(self) -> dict[str, str]:
        child_env = os.environ.copy() if self._inherit_env else {}
        for name, value in self._env.items():
            if value is None:
                child_env.pop(name, None)
            else:
                child_env[name] = value
        # Uvicorn itself accepts environment-based CLI defaults, including an
        # env-file and worker count. Keep process ownership/settings explicit.
        for name in list(child_env):
            if name.startswith("UVICORN_") or name == "WEB_CONCURRENCY":
                child_env.pop(name)
        return child_env

    def start(self) -> ServiceProcess:
        """Return this ready instance; a repeated start reuses its healthy child.

        An occupied explicit port is an error. The helper never attaches to a
        service already listening there and never stops a process it did not own.
        """
        with self._lock:
            if self.is_running:
                if self._healthy():
                    return self
                self.stop()
                raise RuntimeError("The owned service is no longer healthy and has been stopped. Call start() to retry.")
            self.stop()  # Reap a previously exited child before starting again.
            if os.name != "posix":
                raise RuntimeError("ServiceProcess requires Linux or macOS for safe socket-descriptor handoff.")
            if not self.project_dir.is_dir():
                raise ValueError("project_dir must be an existing directory containing the application.")
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    listener.bind(("127.0.0.1", self._requested_port))
                    listener.listen(128)
                except OSError:
                    raise RuntimeError("Cannot reserve the requested loopback port. Choose port=0 or another unused port.") from None
                port = listener.getsockname()[1]
                self._base_url = f"http://127.0.0.1:{port}"
                try:
                    self._process = subprocess.Popen(
                        [sys.executable, "-m", "uvicorn", self.app,
                         "--fd", str(listener.fileno()), "--host", "127.0.0.1",
                         "--workers", "1", "--log-level", "warning", "--no-access-log",
                         *(["--factory"] if self._factory else [])],
                        cwd=self.project_dir,
                        env=self._child_environment(),
                        pass_fds=(listener.fileno(),),
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except (OSError, ValueError, TypeError):
                    raise RuntimeError("Could not launch Uvicorn. Check the Python environment and application settings.") from None
                atexit.register(self.stop)
                self._atexit_registered = True
                deadline = time.monotonic() + self._startup_timeout
                while time.monotonic() < deadline:
                    if not self.is_running:
                        raise RuntimeError("Uvicorn exited before readiness. Check the app import, dependencies and startup settings.")
                    remaining = deadline - time.monotonic()
                    if remaining > 0 and self._healthy(timeout=min(0.25, remaining)):
                        return self
                    time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
                raise RuntimeError("The owned service did not become ready before the timeout. Check its health route and startup settings.")
            except BaseException:
                self.stop()
                raise
            finally:
                # Uvicorn has its own inherited descriptor. The parent must not
                # retain a listening socket once startup has completed or failed.
                listener.close()

    def stop(self) -> None:
        """Terminate and reap only this object's child. Safe to call repeatedly."""
        with self._lock:
            process = self._process
            if process is not None:
                if process.poll() is None:
                    try:
                        process.terminate()
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=5.0)
                    except subprocess.TimeoutExpired:
                        try:
                            process.kill()
                        except ProcessLookupError:
                            pass
                        process.wait(timeout=5.0)
                else:
                    process.wait()
            self._process = None
            self._base_url = None
            if self._atexit_registered:
                atexit.unregister(self.stop)
                self._atexit_registered = False

    def __enter__(self) -> ServiceProcess:
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
