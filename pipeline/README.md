# Pipeline Tools

Structured Maya pipeline tools with MCP (Model Context Protocol) support for Claude Code integration.

## Structure

```
pipeline/
├── STANDARDS.md          ← Development standards for all tools
├── CLAUDE.md             ← Claude Code workflow instructions
├── mcp/                  ← Maya MCP server (connects Claude Code to Maya)
│   ├── maya_mcp_server.py
│   ├── maya_start_port.py
│   ├── requirements.txt
│   └── README.md
├── specs/                ← Tool specifications (write before coding)
│   └── mixamo_rig_builder.md
└── tools/                ← All pipeline tools
    ├── maya_connector/   ← MCP port management for Maya
    ├── mixamo_rig_builder/
    └── _tool_template/   ← Copy this to create new tools
```

## Getting Started

1. **Read STANDARDS.md** — all tools follow these rules
2. **Read CLAUDE.md** — workflow for building tools
3. **Run mcp/setup.sh** or `pip install -r mcp/requirements.txt` to install MCP
4. **Drag any tool .py into Maya** to install shelf button

## Quick Links

- **Maya MCP Setup:** `mcp/README.md`
- **Tool Development:** `CLAUDE.md`
- **Coding Rules:** `STANDARDS.md`

---

**New tools go here** — copy `tools/_tool_template/` to start.
