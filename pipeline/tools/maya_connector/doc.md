# Maya MCP Connector

**Version:** 1.0.0
**Author:** Sachin

---

## What It Does

Opens Maya's built-in command port (TCP socket on port 7001) so Claude Code can connect to a live Maya session and run Python code, read scene data, and build/test tools interactively.

---

## How to Install (share this with teammates)

1. **Install the MCP server dependency** (once per machine):
   ```
   pip install mcp
   ```

2. **Drag `maya_connector.py` into the Maya viewport**
   - A **Pipeline** shelf button appears called **MCP Port**
   - Port 7001 opens automatically
   - An in-viewport message confirms: *"Port 7001 is open"*

3. **Tick "Auto-start port when Maya launches"** in the UI (optional but recommended)
   - Writes a one-liner to your `userSetup.py` so the port opens every time Maya starts

4. **Open Claude Code** in the `maya-tools` folder — it connects automatically

---

## Shelf Button Behaviour

| State | Dot colour | Button |
|-------|-----------|--------|
| Port open | Green ● | Stop Port |
| Port closed | Grey ● | Start Port |

The UI polls every 2 seconds and updates the indicator live.

---

## What Gets Shared With Teammates

They only need two things from this repo:

| File | Purpose |
|------|---------|
| `tools/maya_connector/maya_connector.py` | Drag into Maya to install |
| `mcp/maya_mcp_server.py` | Claude Code runs this automatically |

Everything else (the `Pipeline` shelf, `userSetup.py` entry, port management) is handled automatically on drag-in.

---

## Revision History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial release |
