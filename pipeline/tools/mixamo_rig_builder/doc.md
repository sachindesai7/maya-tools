# Mixamo Rig Builder

**Version:** 1.0.0  
**Author:** Sachin  
**Spec:** `../specs/mixamo_rig_builder.md`  
**Location:** `pipeline/tools/mixamo_rig_builder/`

---

## Repository Structure

```
maya-tools/
└── pipeline/                       ← All new tools and standards
    ├── STANDARDS.md               ← Development rules (required reading)
    ├── CLAUDE.md                  ← Claude Code workflow
    ├── README.md                  ← Quick reference
    ├── mcp/                       ← Maya MCP infrastructure
    │   ├── maya_mcp_server.py     ← Claude Code ↔ Maya bridge
    │   ├── maya_start_port.py     ← One-time setup
    │   ├── requirements.txt        ← pip install mcp
    │   └── README.md
    ├── specs/                     ← Tool specifications
    │   ├── _spec_template.md
    │   └── mixamo_rig_builder.md  ← This tool's spec
    └── tools/                     ← All pipeline tools
        ├── maya_connector/        ← MCP port manager
        ├── mixamo_rig_builder/    ← This tool
        └── _tool_template/        ← Copy to create new tools
```

---

## What It Does

Six-button step-by-step rigging tool. Builds a Mixamo-compatible skeleton from
scratch, creates proxy volumes per bone to define skin coverage, assigns skin
weights from those volumes with boundary gradients, and mirrors everything
left-to-right so you only ever work on the left side.

---

## Workflow

| Button | What to do after |
|--------|-----------------|
| 1. Create Skeleton | Position left-side joints to fit your character |
| 2. Mirror Joints | — (automatic) |
| 3. Create Proxy | Adjust left-side proxy boxes (scale, add loops) |
| 4. Mirror Proxy | — (automatic) |
| 5. Skin | Select mesh first; touch up left-side weights after |
| 6. Mirror Skin | Select mesh first |

---

## Settings

| Setting | Default | Notes |
|---------|---------|-------|
| Proxy base size | 5 units | Width/depth of proxy boxes. Fingers auto-scale to 35% |
| Boundary blend | 10% | Gradient zone at each joint as % of bone length |

---

## Skip List (no proxy box)

`HeadTop_End`, `LeftEye/RightEye`, `LeftToe_End/RightToe_End`,
all fingertip-4 joints (`LeftHandIndex4` etc.)

---

## Skeleton Data

67 joints baked from a real Mixamo rig (T-pose, centimeters).
Root: `mixamorig:Hips`. Namespace: `mixamorig`.

---

## Revision History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial build — skeleton, proxy, skin, mirror |
