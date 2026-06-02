# ─────────────────────────────────────────────────────────────────────────────
# Run this ONCE in Maya's Script Editor (Python tab) to open the MCP port.
# After that, Claude Code can talk to Maya directly.
#
# How to use:
#   1. Open Maya
#   2. Open Script Editor  (Windows → General Editors → Script Editor)
#   3. Switch tab to Python
#   4. Paste this entire file and press Ctrl+Enter (or the Run button)
#   5. You should see "[Maya MCP] Port 7001 is open." in the output
#
# To auto-open on every Maya start, save this to:
#   Documents/maya/<version>/scripts/userSetup.py
# ─────────────────────────────────────────────────────────────────────────────

import maya.cmds as cmds

MCP_PORT = 7001

def open_mcp_port(port=MCP_PORT):
    port_str = f":{port}"

    # Close existing port first to avoid "port already in use" errors
    try:
        if cmds.commandPort(port_str, query=True):
            cmds.commandPort(port_str, close=True)
            print(f"[Maya MCP] Closed existing port {port}.")
    except Exception:
        pass

    cmds.commandPort(
        name=port_str,
        sourceType="python",
        echoOutput=False,
        noreturn=False,
    )
    print(f"[Maya MCP] Port {port} is open. Claude Code can now connect.")

open_mcp_port()
