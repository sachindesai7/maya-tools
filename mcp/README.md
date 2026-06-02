# Maya MCP Server

Lets Claude Code talk directly to a running Maya session.

---

## Architecture

```
Claude Code  ──MCP──►  maya_mcp_server.py  ──TCP:7001──►  Maya commandPort
```

---

## One-time Setup

### 1. Install the MCP server dependency

Open a terminal in the `maya-tools` folder:

```bash
pip install mcp
```

### 2. Open the Maya port (do this each time Maya starts)

1. Open Maya
2. Open **Script Editor** → `Windows → General Editors → Script Editor`
3. Switch to the **Python** tab
4. Open `mcp/maya_start_port.py`, paste it in, press **Ctrl+Enter**
5. You should see: `[Maya MCP] Port 7001 is open.`

**To make this automatic on every Maya launch**, copy the contents of `maya_start_port.py` into:
```
Documents/maya/<version>/scripts/userSetup.py
```

### 3. Open Claude Code in this project

```bash
cd C:/Users/Sachin/maya-tools
claude
```

Claude Code reads `.claude/settings.json` and starts the MCP server automatically.
You'll see `maya` listed in the MCP tools panel.

---

## What Claude Can Do Once Connected

| Tool | What it does |
|------|-------------|
| `execute_python` | Run any Python code inside Maya (cmds, API, PySide2) |
| `get_scene_info` | Get all objects, current selection, frame, scene name |
| `get_selection` | Get current selection as a list |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Could not connect to Maya on port 7001` | Run `maya_start_port.py` in Maya Script Editor |
| `Port already in use` | Run `maya_start_port.py` again — it closes the old port first |
| `Maya did not respond within 30 seconds` | Your code ran too long or hung — check Maya's Script Editor output |
| MCP server not showing in Claude Code | Make sure `pip install mcp` ran, then restart Claude Code |

---

## Sharing With Teammates

Everything needed is in this repo:
- `mcp/maya_mcp_server.py` — the server
- `mcp/maya_start_port.py` — open port inside Maya
- `mcp/requirements.txt` — `pip install -r mcp/requirements.txt`
- `.claude/settings.json` — Claude Code picks this up automatically

They only need to update the `cwd` path in `.claude/settings.json` to their local path.
