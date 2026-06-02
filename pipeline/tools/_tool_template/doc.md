# Tool Name

**Version:** 1.0.0  
**Author:** Sachin  
**Spec:** `../../specs/tool_name.md`  
**Location:** `pipeline/tools/tool_name/`

---

## Repository Structure

```
maya-tools/
└── pipeline/                       ← All tools and standards
    ├── STANDARDS.md               ← Development rules (read first!)
    ├── CLAUDE.md                  ← Claude Code workflow
    ├── README.md                  ← Quick reference
    ├── mcp/                       ← Maya MCP infrastructure
    │   ├── maya_mcp_server.py     ← Claude Code ↔ Maya bridge
    │   ├── maya_start_port.py     ← Setup script
    │   ├── requirements.txt
    │   └── README.md
    ├── specs/                     ← Tool specifications (one per tool)
    │   └── tool_name.md           ← This tool's spec
    └── tools/                     ← All pipeline tools
        ├── tool_name/             ← This tool
        │   ├── tool_name.py       ← Main code
        │   ├── icon.png           ← Shelf icon (64x64 PNG)
        │   └── doc.md             ← This file
        └── _tool_template/        ← Copy this to create new tools
```

---

## What It Does

One paragraph plain English description.

---

## Inputs

| Input | Type | Description |
|-------|------|-------------|
| Selection | mesh | The mesh(es) to operate on |
| Count | int (1–10) | How many ... |

---

## Outputs

| Output | Naming Pattern | Notes |
|--------|---------------|-------|
| LOD groups | `{mesh}_LOD0`, `{mesh}_LOD1` | Parented under `{mesh}_LOD_GRP` |

---

## Logic Flow

1. Validate selection — must have at least one mesh selected
2. ...
3. ...
4. Show in-viewport confirmation

---

## Edge Cases

| Situation | Behaviour |
|-----------|-----------|
| Nothing selected | In-viewport warning, exit early |
| Non-mesh selected | Skip with cmds.warning |
| Tool run twice | Existing LOD group replaced, not duplicated |

---

## Revision History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial build |
