# Claude Code Instructions — Maya Tools Repo

## Always Read First

Before writing any tool, read `STANDARDS.md` in full. Every rule in that file is non-negotiable.

## What This Repo Is

Maya pipeline tools written in Python for Autodesk Maya. Tools include things like LOD generators, rig builders, foot sliders, corrective shape managers, etc.

## When Asked to Build a New Tool

1. Read the spec file in `specs/` for that tool.
2. Read `STANDARDS.md`.
3. Write a design doc in `docs/<tool_name>_design.md` covering:
   - What the tool does in plain English
   - Inputs (selection type, UI controls)
   - Outputs (what nodes/groups get created, naming pattern)
   - Step-by-step logic flow
   - Edge cases and how to handle them
4. Wait for confirmation before coding.
5. Write the tool in `tools/<tool_name>.py` following STANDARDS.md exactly.
6. Run through the pre-commit checklist in STANDARDS.md section 15.

## When Asked to Review a Tool

Check in this order:
1. Does `onMayaDroppedPythonFile` exist and call `_install_shelf_button()`?
2. Does `_install_shelf_button()` correctly find/create the shelf and avoid duplicates?
3. Is the undo chunk properly wrapped in try/finally?
4. Is selection validated before any scene modification?
5. Are there any hardcoded paths?
6. Are there any `print()` statements?
7. Is PySide2 used (not PyQt5)?
8. Is `TOOL_VERSION` set?

## Maya-Specific Rules to Enforce

- API 2.0 (`maya.api.OpenMaya`) only — never API 1.0 (`maya.OpenMaya`)
- `maya.cmds` for simple ops, API 2.0 for performance-critical loops
- UI must parent to Maya main window via `MQtUtil.mainWindow()` + `wrapInstance`
- Node naming must follow the convention in STANDARDS.md section 10
- Never use `cmds.select(clear=True)` mid-operation without restoring selection after

## Shelf Button Behaviour Expected

When a `.py` tool file is dragged into Maya's viewport:
- `onMayaDroppedPythonFile` fires
- A "Pipeline" shelf tab is created if it doesn't exist
- Any existing button with the same label is removed first
- A new shelf button is added that calls `show()` on the tool
- An in-viewport message confirms installation

## File Layout

```
maya-tools/
├── STANDARDS.md                    ← coding rules
├── CLAUDE.md                       ← this file
├── specs/                          ← one .md per tool (the "ticket")
└── tools/
    ├── lod_generator/
    │   ├── lod_generator.py        ← tool file (name matches folder)
    │   ├── icon.png                ← 64x64 PNG shelf icon
    │   └── doc.md                  ← design doc (lives with the tool)
    ├── foot_slider/
    │   ├── foot_slider.py
    │   ├── icon.png
    │   └── doc.md
    └── _tool_template/             ← copy this to start any new tool
        ├── _tool_template.py
        ├── icon.png
        └── doc.md
```

When creating a new tool:
1. Copy the `_tool_template` folder.
2. Rename the folder and `.py` file to the new tool name.
3. Update the metadata block at the top of `.py`.
4. Write `doc.md` first — get it reviewed — then write the code.
