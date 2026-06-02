# Tool Spec: Mixamo Rig Builder

## What It Does
A step-by-step rigging tool for Mixamo-compatible characters. Builds the standard
Mixamo skeleton, creates proxy boxes for each bone to define skin volume, assigns
skin weights from those boxes, smooths at bone boundaries, and mirrors everything
left-to-right. The user works only on the left side; the tool handles the right.

## Workflow (in order)

### Step 1 — Create Skeleton
Press "Create Skeleton" → tool creates the full standard Mixamo joint hierarchy
(67 joints) under `mixamorig:Hips` with correct naming and parent-child structure.
If a Mixamo skeleton already exists in the scene, skip creation and use the existing one.

### Step 2 — Mirror Left → Right (Joints)
User positions left-side joints manually.
Press "Mirror Joints" → tool mirrors all `Left` joints to `Right` using
`cmds.mirrorJoint` with `mirrorYZ=True, mirrorBehavior=True`.

### Step 3 — Create Proxy Boxes
Press "Create Proxy Boxes" → for each joint (except skipped ones), create a cube
aligned to the bone with:
- Length = distance to first child joint
- Width/Height = user-defined base size (default 5 units), adjustable per-box
- Named: `proxy_{joint_short_name}`
- Grouped under `proxy_GRP`

**Skip these joints (no proxy box):**
- Any joint ending in `_End` (e.g. `HeadTop_End`, `LeftToe_End`)
- Eye joints (`LeftEye`, `RightEye`)

**Include fingers:** All finger joints get proxy boxes (small ones).

### Step 4 — Mirror Left → Right (Proxy Boxes)
User adjusts left-side proxy box sizes and shapes (add loops, scale, etc.).
Press "Mirror Proxy" → tool copies scale, shape, and loop count from each
Left proxy box to its Right counterpart.

### Step 5 — Skin
User selects the character mesh, then presses "Skin".
Tool:
1. Binds mesh to skeleton (`cmds.skinCluster`, max influences=4, method=distance)
2. For each non-skipped joint: assigns 100% weight to all vertices inside or
   overlapping its proxy box (using a bounding-box vertex test)
3. At bone boundaries (vertices within 10% of bone length from the joint):
   blends weights as a gradient between parent and child bone — short falloff,
   not full-length
4. Deletes all proxy boxes and `proxy_GRP` after skinning is complete

### Step 6 — Mirror Skin Weights (Left → Right)
User touches up left-side weights in the weight editor.
Press "Mirror Skin" → runs `cmds.copySkinWeights` with `mirrorMode='YZ'`
to copy left weights to right.

## Inputs

| Input | Type | Default |
|-------|------|---------|
| Proxy box base size | float (units) | 5.0 |
| Boundary blend distance | % of bone length | 10% |
| Max skin influences | int | 4 |
| Character mesh | selection | — |

## Outputs
- Mixamo joint hierarchy (`mixamorig:Hips` root, 67 joints)
- SkinCluster on character mesh
- Proxy boxes deleted after skinning

## Skip List (no proxy box)
- `mixamorig:HeadTop_End`
- `mixamorig:LeftEye` / `mixamorig:RightEye`
- `mixamorig:LeftToe_End` / `mixamorig:RightToe_End`
- `mixamorig:LeftHandIndex4` / RightHandIndex4
- `mixamorig:LeftHandMiddle4` / RightHandMiddle4
- `mixamorig:LeftHandPinky4` / RightHandPinky4
- `mixamorig:LeftHandRing4` / RightHandRing4
- `mixamorig:LeftHandThumb4` / RightHandThumb4

## UI Layout
Six buttons across the top in workflow order:
```
[ Create Skeleton ] [ Mirror Joints ] [ Create Proxy ] [ Mirror Proxy ] [ Skin ] [ Mirror Skin ]
```
Below: proxy base size slider, boundary blend % slider.
Status line at bottom showing current step.

## Edge Cases
| Situation | Behaviour |
|-----------|-----------|
| Skeleton already exists | Skip creation, warn in Script Editor |
| No mesh selected on Skin | In-viewport warning, abort |
| Proxy box covers no vertices | Skip that bone, warn |
| Mirror run twice | Existing right-side proxies replaced |

## Maya Icon
`ikHandle.png`

## Shelf Label
`Mixamo\nRig`
