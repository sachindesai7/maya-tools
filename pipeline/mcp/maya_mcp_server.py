#!/usr/bin/env python3
"""
Maya MCP Server — FastMCP bridge to Maya's commandPort.

Maya's commandPort never reliably returns stdout from multi-line scripts.
We sidestep this by writing output to a temp file that both Maya and this
server can access (same machine), then reading it back.
"""

import os
import socket
import tempfile
import time
from mcp.server.fastmcp import FastMCP

MAYA_HOST = "localhost"
MAYA_PORT = 7001
TIMEOUT   = 30

mcp = FastMCP("maya")


# ── Socket layer ───────────────────────────────────────────────────────────────

def _raw_send(code: str) -> None:
    """Send code to Maya's commandPort. Return value is ignored."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(TIMEOUT)
            sock.connect((MAYA_HOST, MAYA_PORT))
            sock.sendall(code.encode("utf-8"))
            # Drain the socket so Maya doesn't block
            while True:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    break
                if not chunk or b"\x00" in chunk:
                    break
    except ConnectionRefusedError:
        raise RuntimeError("Cannot connect to Maya on port 7001. Run maya_start_port.py in Maya's Script Editor.")
    except socket.timeout:
        raise RuntimeError("Maya did not respond within 30 seconds.")


def _send_to_maya(code: str) -> str:
    """
    Execute Python code in Maya and return its stdout output.
    Writes output to a temp file — avoids Maya commandPort return-value quirks.
    """
    tmp = tempfile.mktemp(suffix=".txt", prefix="maya_mcp_")

    wrapped = "\n".join([
        "import sys as _sys, io as _io, traceback as _tb",
        f"_tmp = r'{tmp}'",
        "_buf = _io.StringIO()",
        "_sys.stdout = _buf",
        "try:",
        f"    exec(compile({repr(code)}, '<maya-mcp>', 'exec'), globals())",
        "    _out = _buf.getvalue()",
        "except Exception:",
        "    _out = _tb.format_exc()",
        "finally:",
        "    _sys.stdout = _sys.__stdout__",
        "open(_tmp, 'w', encoding='utf-8').write(_out)",
    ])

    try:
        _raw_send(wrapped)
    except RuntimeError as e:
        return str(e)

    # Wait for Maya to finish writing
    for _ in range(30):
        if os.path.exists(tmp):
            break
        time.sleep(0.1)

    try:
        with open(tmp, "r", encoding="utf-8") as f:
            result = f.read()
        os.remove(tmp)
        return result
    except FileNotFoundError:
        return "ERROR: Maya did not write a result. Check that Maya is running and the command port is open."
    except Exception as e:
        return f"ERROR reading result file: {e}"


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def execute_python(code: str) -> str:
    """Execute Python code in the running Maya session. Use print() to return values."""
    return _send_to_maya(code) or "(no output)"


@mcp.tool()
def get_scene_info() -> str:
    """Return a JSON summary of the Maya scene: objects, selection, current frame, scene name."""
    code = "\n".join([
        "import maya.cmds as cmds, json",
        "print(json.dumps({",
        '    "scene_name":    cmds.file(query=True, sceneName=True) or "untitled",',
        '    "current_frame": cmds.currentTime(query=True),',
        '    "selection":     cmds.ls(selection=True) or [],',
        '    "all_objects":   cmds.ls(dag=True) or [],',
        "}, indent=2))",
    ])
    return _send_to_maya(code)


@mcp.tool()
def get_selection() -> str:
    """Return the current Maya selection as a JSON list of node names."""
    code = "import maya.cmds as cmds, json; print(json.dumps(cmds.ls(selection=True, long=True) or []))"
    return _send_to_maya(code)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
