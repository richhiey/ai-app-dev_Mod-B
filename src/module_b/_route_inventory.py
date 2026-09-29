"""Read registered POST paths from trusted student source in an isolated process."""
import contextlib
import io
import json
import socket
import sys
from unittest.mock import patch

sys.path.insert(0,sys.argv[1])
def blocked(*args,**kwargs):
    raise RuntimeError('Network disabled during route inspection.')
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
     patch.object(socket.socket,'connect',blocked), patch.object(socket.socket,'connect_ex',blocked), \
     patch.object(socket,'create_connection',blocked):
    from app.main import app
    from module_b.security import protected_post_paths
    paths=list(protected_post_paths(app))
print(json.dumps(paths))
