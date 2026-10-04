"""Private child entry point: report bounded diagnosis codes, never raw logs."""
from __future__ import annotations

import os
import sys


def diagnosis(exc: BaseException) -> str:
    # Only fixed categories cross the pipe. Exception text, request bodies,
    # headers and arbitrary exception-class names never leave the child.
    cls = type(exc)
    if cls.__module__ == "module_b.openrouter" and cls.__name__ == "OpenRouterError":
        from module_b._startup_diagnostics import PROVIDER_FAILURES
        return exc.kind if exc.kind in PROVIDER_FAILURES else "provider_error"
    if cls.__module__ == "module_b.retrieval" and cls.__name__ == "ChromaStorageError":
        return "storage"
    if isinstance(exc, ModuleNotFoundError):
        return "missing_module"
    if isinstance(exc, ImportError):
        return "import_error"
    if isinstance(exc, SyntaxError):
        return "syntax_error"
    if isinstance(exc, PermissionError):
        return "permission"
    if isinstance(exc, FileNotFoundError):
        return "missing_file"
    if isinstance(exc, (TypeError, ValueError)):
        return "configuration"
    return "application_error"


def main() -> None:
    target, socket_fd, report_fd, factory = sys.argv[1:]
    report_fd = int(report_fd)
    reported = False

    def report(stage: str, code: str) -> None:
        nonlocal reported
        if reported:
            return
        reported = True
        try:
            os.write(report_fd, (stage + ":" + code).encode("ascii"))
        except OSError:
            pass  # Parent may have timed out and closed its end.

    stage = "import"
    try:
        import uvicorn
        from uvicorn.importer import import_from_string
        application = import_from_string(target)
        stage = "factory"
        if factory == "1":
            application = application()
        stage = "startup"

        async def observed_app(scope, receive, send):
            if scope["type"] != "lifespan":
                return await application(scope, receive, send)
            failed = False
            started = False

            async def observed_send(message):
                nonlocal failed, started
                if message["type"] == "lifespan.startup.failed":
                    failed = True
                elif message["type"] == "lifespan.startup.complete":
                    started = True
                await send(message)

            try:
                await application(scope, receive, observed_send)
            except BaseException as exc:
                if not started:
                    report("startup", diagnosis(exc))
                raise
            finally:
                if failed:
                    report("startup", "application_error")

        uvicorn.run(observed_app, fd=int(socket_fd), host="127.0.0.1",
                    workers=1, log_level="warning", access_log=False,
                    lifespan="on")
    except BaseException as exc:
        report(stage, diagnosis(exc))
        raise
    finally:
        os.close(report_fd)


if __name__ == "__main__":
    main()
