# Tool Name

**Version:** 1.0.0  
**Author:** Sachin  
**Spec:** `specs/tool_name.md`

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
