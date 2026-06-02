"""
Mixamo Rig Builder — builds a Mixamo-compatible skeleton from scratch,
creates proxy skin volumes per bone, assigns skin weights from those volumes,
smooths at bone boundaries, and mirrors everything left-to-right.
"""

# ── TOOL METADATA ─────────────────────────────────────────────────────────────
TOOL_NAME        = "mixamo_rig_builder"
TOOL_LABEL       = "Mixamo\nRig"
TOOL_DESCRIPTION = "Build Mixamo skeleton, proxy boxes, and skin weights step by step"
TOOL_VERSION     = "1.0.1"
TOOL_AUTHOR      = "Sachin"
TOOL_ICON        = "icon.png"
SHELF_NAME       = "Pipeline"
# ──────────────────────────────────────────────────────────────────────────────

import os
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance

_TOOL_DIR  = os.path.dirname(os.path.abspath(__file__))
NAMESPACE  = "mixamorig"
PROXY_GRP  = "proxy_GRP"
PROXY_ATTR = "proxyForJoint"   # string attribute stored on every proxy cube

# ── Skip list — no proxy box for these joints ─────────────────────────────────
SKIP_PROXY = frozenset([
    "mixamorig:HeadTop_End",
    "mixamorig:LeftEye",           "mixamorig:RightEye",
    "mixamorig:LeftToe_End",       "mixamorig:RightToe_End",
    "mixamorig:LeftHandIndex4",    "mixamorig:RightHandIndex4",
    "mixamorig:LeftHandMiddle4",   "mixamorig:RightHandMiddle4",
    "mixamorig:LeftHandPinky4",    "mixamorig:RightHandPinky4",
    "mixamorig:LeftHandRing4",     "mixamorig:RightHandRing4",
    "mixamorig:LeftHandThumb4",    "mixamorig:RightHandThumb4",
])

# ── Baked Mixamo skeleton (captured from live rig) ────────────────────────────
JOINT_DATA = {
    "mixamorig:Head":             {"parent": "mixamorig:Neck",              "pos": [0.9987,   333.4852,  1.4132],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:HeadTop_End":      {"parent": "mixamorig:Head",              "pos": [1.1526,   371.7975, 12.2396],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:Hips":             {"parent": None,                          "pos": [-0.0418,  209.0796, -1.4166],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftArm":          {"parent": "mixamorig:LeftShoulder",      "pos": [38.5987,  299.8648,-10.238],   "orient": [1.6884,   0.0,      8.7724],    "radius": 3.0},
    "mixamorig:LeftEye":          {"parent": "mixamorig:Head",              "pos": [7.0842,   350.2215, 18.1736],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftFoot":         {"parent": "mixamorig:LeftLeg",           "pos": [18.5268,   24.666,  -5.4092],  "orient": [51.9779, -3.7491,   2.625],     "radius": 3.0},
    "mixamorig:LeftForeArm":      {"parent": "mixamorig:LeftArm",           "pos": [93.7264,  299.8648,-10.2381],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHand":         {"parent": "mixamorig:LeftForeArm",       "pos": [146.4997, 299.8648,-10.2382],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandIndex1":   {"parent": "mixamorig:LeftHand",          "pos": [174.99,   299.4089, -5.0863],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandIndex2":   {"parent": "mixamorig:LeftHandIndex1",    "pos": [182.0528, 299.4089, -5.0863],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandIndex3":   {"parent": "mixamorig:LeftHandIndex2",    "pos": [188.5481, 299.4089, -5.0862],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandIndex4":   {"parent": "mixamorig:LeftHandIndex3",    "pos": [195.1415, 299.4089, -5.0862],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandMiddle1":  {"parent": "mixamorig:LeftHand",          "pos": [174.2443, 299.8648,-10.2382],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandMiddle2":  {"parent": "mixamorig:LeftHandMiddle1",   "pos": [181.1759, 299.8648,-10.2382],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandMiddle3":  {"parent": "mixamorig:LeftHandMiddle2",   "pos": [187.9995, 299.8648,-10.2382],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandMiddle4":  {"parent": "mixamorig:LeftHandMiddle3",   "pos": [195.3922, 299.8648,-10.2383],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandPinky1":   {"parent": "mixamorig:LeftHand",          "pos": [168.4055, 299.4259,-19.0192],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandPinky2":   {"parent": "mixamorig:LeftHandPinky1",    "pos": [174.9422, 299.4258,-19.0192],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandPinky3":   {"parent": "mixamorig:LeftHandPinky2",    "pos": [179.0913, 299.4258,-19.0192],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandPinky4":   {"parent": "mixamorig:LeftHandPinky3",    "pos": [184.6548, 299.4258,-19.0192],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandRing1":    {"parent": "mixamorig:LeftHand",          "pos": [171.9838, 299.9451,-14.4792],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandRing2":    {"parent": "mixamorig:LeftHandRing1",     "pos": [178.2937, 299.945, -14.4792],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandRing3":    {"parent": "mixamorig:LeftHandRing2",     "pos": [184.6532, 299.945, -14.4792],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandRing4":    {"parent": "mixamorig:LeftHandRing3",     "pos": [191.691,  299.945, -14.4792],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandThumb1":   {"parent": "mixamorig:LeftHand",          "pos": [157.6229, 296.5719, -4.1101],  "orient": [27.3116, -12.921,  23.4134],    "radius": 3.0},
    "mixamorig:LeftHandThumb2":   {"parent": "mixamorig:LeftHandThumb1",    "pos": [166.3172, 291.5522,  0.9095],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandThumb3":   {"parent": "mixamorig:LeftHandThumb2",    "pos": [173.2542, 287.5472,  4.9146],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftHandThumb4":   {"parent": "mixamorig:LeftHandThumb3",    "pos": [177.7426, 284.9558,  7.5059],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftLeg":          {"parent": "mixamorig:LeftUpLeg",         "pos": [18.0761,  109.9968,  0.9836],  "orient": [-2.4312,  0.0128,   0.5747],    "radius": 3.0},
    "mixamorig:LeftShoulder":     {"parent": "mixamorig:Spine2",            "pos": [12.3379,  299.0871, -6.1838],  "orient": [127.3906,101.4038,  39.6061],   "radius": 3.0},
    "mixamorig:LeftToeBase":      {"parent": "mixamorig:LeftFoot",          "pos": [21.2193,    3.2711, 18.8815],  "orient": [42.1217,  0.6643,  -5.4895],    "radius": 3.0},
    "mixamorig:LeftToe_End":      {"parent": "mixamorig:LeftToeBase",       "pos": [20.8897,    3.5216, 37.9418],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:LeftUpLeg":        {"parent": "mixamorig:Hips",              "pos": [18.4825,  195.241,   1.2455],  "orient": [-1.0155, -0.0048, 179.7269],    "radius": 3.0},
    "mixamorig:Neck":             {"parent": "mixamorig:Spine2",            "pos": [-0.0431,  311.2542, -5.1003],  "orient": [9.412,   -0.1955,  -1.6145],    "radius": 3.0},
    "mixamorig:RightArm":         {"parent": "mixamorig:RightShoulder",     "pos": [-39.5889, 299.8649,-12.1041],  "orient": [1.0027,   0.0,    -11.634],     "radius": 3.0},
    "mixamorig:RightEye":         {"parent": "mixamorig:Head",              "pos": [-5.1182,  349.9611, 17.8702],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightFoot":        {"parent": "mixamorig:RightLeg",          "pos": [-18.5268,  24.6662, -5.4083],  "orient": [52.4439,  4.3548,  -2.9429],    "radius": 3.0},
    "mixamorig:RightForeArm":     {"parent": "mixamorig:RightArm",          "pos": [-95.4316, 299.8649,-12.104],   "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHand":        {"parent": "mixamorig:RightForeArm",      "pos": [-145.7453,299.8648,-12.104],   "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandIndex1":  {"parent": "mixamorig:RightHand",         "pos": [-172.3483,299.3179, -6.9974],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandIndex2":  {"parent": "mixamorig:RightHandIndex1",   "pos": [-179.4405,299.3179, -6.9974],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandIndex3":  {"parent": "mixamorig:RightHandIndex2",   "pos": [-186.8549,299.3179, -6.9974],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandIndex4":  {"parent": "mixamorig:RightHandIndex3",   "pos": [-192.3774,299.3179, -6.9973],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandMiddle1": {"parent": "mixamorig:RightHand",         "pos": [-171.8109,299.8649,-12.104],   "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandMiddle2": {"parent": "mixamorig:RightHandMiddle1",  "pos": [-177.9708,299.8649,-12.1039],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandMiddle3": {"parent": "mixamorig:RightHandMiddle2",  "pos": [-185.2499,299.8648,-12.1039],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandMiddle4": {"parent": "mixamorig:RightHandMiddle3",  "pos": [-192.7099,299.8648,-12.1039],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandPinky1":  {"parent": "mixamorig:RightHand",         "pos": [-166.7347,299.368, -20.6451],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandPinky2":  {"parent": "mixamorig:RightHandPinky1",   "pos": [-172.6743,299.368, -20.6452],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandPinky3":  {"parent": "mixamorig:RightHandPinky2",   "pos": [-176.439, 299.368, -20.6452],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandPinky4":  {"parent": "mixamorig:RightHandPinky3",   "pos": [-182.8094,299.368, -20.6452],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandRing1":   {"parent": "mixamorig:RightHand",         "pos": [-169.8325,299.8666,-16.0879],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandRing2":   {"parent": "mixamorig:RightHandRing1",    "pos": [-176.69,  299.8667,-16.0879],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandRing3":   {"parent": "mixamorig:RightHandRing2",    "pos": [-183.5255,299.8666,-16.0879],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandRing4":   {"parent": "mixamorig:RightHandRing3",    "pos": [-189.5427,299.8667,-16.0878],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandThumb1":  {"parent": "mixamorig:RightHand",         "pos": [-155.2473,295.9342, -5.9473],  "orient": [27.3119,  12.9212, -23.4135],   "radius": 3.0},
    "mixamorig:RightHandThumb2":  {"parent": "mixamorig:RightHandThumb1",   "pos": [-163.2637,291.3059, -1.3191],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandThumb3":  {"parent": "mixamorig:RightHandThumb2",   "pos": [-169.9056,287.4712,  2.5156],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightHandThumb4":  {"parent": "mixamorig:RightHandThumb3",   "pos": [-174.6608,284.7258,  5.261],   "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightLeg":         {"parent": "mixamorig:RightUpLeg",        "pos": [-17.9329, 109.8707,  0.6177],  "orient": [-4.1389, -0.0288,  -0.7684],    "radius": 3.0},
    "mixamorig:RightShoulder":    {"parent": "mixamorig:Spine2",            "pos": [-13.2535, 299.4075, -6.681],   "orient": [-59.0042,-76.5017, 149.7625],   "radius": 3.0},
    "mixamorig:RightToeBase":     {"parent": "mixamorig:RightFoot",         "pos": [-21.6805,   3.1751, 19.4099],  "orient": [41.2752,  5.2756,  -0.493],     "radius": 3.0},
    "mixamorig:RightToe_End":     {"parent": "mixamorig:RightToeBase",      "pos": [-24.4117,   3.3999, 38.9207],  "orient": [0.0,      0.0,      0.0],       "radius": 3.0},
    "mixamorig:RightUpLeg":       {"parent": "mixamorig:Hips",              "pos": [-18.4821, 194.6679, -1.2563],  "orient": [0.6773,  -0.0044,-179.629],     "radius": 3.0},
    "mixamorig:Spine":            {"parent": "mixamorig:Hips",              "pos": [-0.2366,  228.8844, -5.3063],  "orient": [-5.735,   0.0,      0.6593],    "radius": 3.0},
    "mixamorig:Spine1":           {"parent": "mixamorig:Spine",             "pos": [-0.507,   252.3847, -7.6666],  "orient": [3.2734,   0.0434,  -0.4323],    "radius": 3.0},
    "mixamorig:Spine2":           {"parent": "mixamorig:Spine1",            "pos": [-0.6162,  280.1923, -8.862],   "orient": [9.3647,   0.055,   -1.2805],    "radius": 3.0},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _topo_sorted():
    """Return joint names in parent-before-child order."""
    ordered, visited = [], set()
    def visit(name):
        if name in visited: return
        visited.add(name)
        parent = JOINT_DATA[name]['parent']
        if parent and parent in JOINT_DATA:
            visit(parent)
        ordered.append(name)
    for n in JOINT_DATA:
        visit(n)
    return ordered


def _left_to_right(name):
    return name.replace('Left', 'Right')


def _proxy_name(joint):
    return 'proxy_' + joint.split(':')[-1]


def _is_finger(joint):
    return any(x in joint for x in ['HandIndex', 'HandMiddle', 'HandPinky', 'HandRing', 'HandThumb'])


# ── Step 1: Create Skeleton ───────────────────────────────────────────────────

ROOT_GRP = 'mixamo_root_GRP'

def create_skeleton():
    """Build center + left Mixamo joints only. Right side is created by Mirror Joints."""
    if cmds.objExists('mixamorig:Hips'):
        cmds.warning('[mixamo_rig_builder] Skeleton already exists — skipping creation.')
        return

    cmds.undoInfo(openChunk=True, chunkName='create_skeleton')
    try:
        if not cmds.namespace(exists=NAMESPACE):
            cmds.namespace(add=NAMESPACE)
        cmds.namespace(set=':' + NAMESPACE)

        # Only create center joints + left-side joints (right side created by mirror)
        center_and_left = {n: d for n, d in JOINT_DATA.items() if 'Right' not in n}

        created = {}
        for name in _topo_sorted():
            if name not in center_and_left:
                continue
            data  = JOINT_DATA[name]
            short = name.split(':')[-1]
            cmds.select(clear=True)
            cmds.joint(name=short, position=data['pos'], radius=data['radius'])
            full  = NAMESPACE + ':' + short
            cmds.setAttr(full + '.jointOrientX', data['orient'][0])
            cmds.setAttr(full + '.jointOrientY', data['orient'][1])
            cmds.setAttr(full + '.jointOrientZ', data['orient'][2])
            created[name] = full

        # Reparent to build hierarchy
        cmds.namespace(set=':')
        for name in center_and_left:
            parent = JOINT_DATA[name]['parent']
            if parent and parent in created:
                cmds.parent(created[name], created[parent])

        # Wrap Hips in a root group so the whole skeleton can be scaled
        if cmds.objExists(ROOT_GRP):
            cmds.delete(ROOT_GRP)
        root_grp = cmds.group(empty=True, name=ROOT_GRP)
        cmds.parent('mixamorig:Hips', root_grp)

        cmds.inViewMessage(
            assistMessage='<b>Skeleton created.</b> Scale <hl>mixamo_root_GRP</hl> to fit your character. '
                          'Position LEFT joints, then Mirror Joints.',
            position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] create_skeleton failed: {e}')
    finally:
        cmds.namespace(set=':')
        cmds.undoInfo(closeChunk=True)


# ── Step 2: Mirror Joints ─────────────────────────────────────────────────────

def mirror_joints():
    """Mirror Left joints to Right. Deletes existing Right joints first to avoid duplicates."""
    cmds.undoInfo(openChunk=True, chunkName='mirror_joints')
    try:
        # Delete any existing right-side joints to avoid duplicates
        right_roots = ['mixamorig:RightUpLeg', 'mixamorig:RightShoulder', 'mixamorig:RightEye']
        for r in right_roots:
            if cmds.objExists(r):
                cmds.delete(r)

        # Mirror left leg, arm/shoulder, and eye chains (LeftArm skipped — it's inside LeftShoulder)
        for left_root in ['mixamorig:LeftUpLeg', 'mixamorig:LeftShoulder', 'mixamorig:LeftEye']:
            if cmds.objExists(left_root):
                cmds.mirrorJoint(left_root, mirrorYZ=True, mirrorBehavior=True,
                                 searchReplace=['Left', 'Right'])

        cmds.inViewMessage(assistMessage='<b>Joints mirrored</b> Left → Right. Now Create Proxy boxes.',
                           position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] mirror_joints failed: {e}')
    finally:
        cmds.undoInfo(closeChunk=True)


# ── Step 3: Create Proxy Boxes ────────────────────────────────────────────────

def create_proxy_boxes(base_size=5.0):
    """Create a proxy cube for each joint (except skip list), aligned along the bone."""
    if cmds.objExists(PROXY_GRP):
        cmds.delete(PROXY_GRP)
    cmds.group(empty=True, name=PROXY_GRP)

    cmds.undoInfo(openChunk=True, chunkName='create_proxy_boxes')
    try:
        joints = cmds.ls('mixamorig:*', type='joint') or []
        for joint in joints:
            if joint in SKIP_PROXY:
                continue

            children = cmds.listRelatives(joint, children=True, type='joint') or []
            pos1 = om.MVector(*cmds.xform(joint, q=True, ws=True, t=True))

            if children:
                pos2   = om.MVector(*cmds.xform(children[0], q=True, ws=True, t=True))
                length = (pos2 - pos1).length()
                mid    = pos1 + (pos2 - pos1) * 0.5
            else:
                length = base_size * 1.5
                mid    = pos1 + om.MVector(0, length * 0.5, 0)

            size = base_size * 0.35 if _is_finger(joint) else base_size
            length = max(length, 1.0)

            pname = _proxy_name(joint)
            cube, _ = cmds.polyCube(w=size, h=length, d=size, name=pname)
            cmds.xform(cube, ws=True, t=[mid.x, mid.y, mid.z])

            if children:
                ac = cmds.aimConstraint(children[0], cube, aimVector=[0, 1, 0],
                                        upVector=[1, 0, 0], worldUpType='scene')
                cmds.delete(ac)

            # Store which joint this proxy belongs to
            cmds.addAttr(cube, longName=PROXY_ATTR, dataType='string')
            cmds.setAttr(cube + '.' + PROXY_ATTR, joint, type='string')

            cmds.parent(cube, PROXY_GRP)

        # Tint proxy boxes cyan so they stand out — stays fully selectable
        cmds.setAttr(PROXY_GRP + '.overrideEnabled', 1)
        cmds.setAttr(PROXY_GRP + '.overrideColor', 18)   # 18 = cyan in Maya's color index

        cmds.inViewMessage(
            assistMessage='<b>Proxy boxes created.</b> '
                          'Adjust LEFT-side boxes to fit your mesh, then Mirror Proxy.',
            position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] create_proxy_boxes failed: {e}')
    finally:
        cmds.undoInfo(closeChunk=True)


# ── Step 4: Mirror Proxy ──────────────────────────────────────────────────────

def mirror_proxy():
    """Copy shape of each Left proxy box to its Right counterpart (mirror across X=0)."""
    if not cmds.objExists(PROXY_GRP):
        cmds.warning('[mixamo_rig_builder] No proxy_GRP found — run Create Proxy first.')
        return

    cmds.undoInfo(openChunk=True, chunkName='mirror_proxy')
    try:
        proxies      = cmds.listRelatives(PROXY_GRP, children=True, type='transform') or []
        left_proxies = [p for p in proxies if 'Left' in p]
        count        = 0

        for left_p in left_proxies:
            if not cmds.attributeQuery(PROXY_ATTR, node=left_p, exists=True):
                continue
            right_p     = _left_to_right(left_p)
            right_joint = _left_to_right(cmds.getAttr(left_p + '.' + PROXY_ATTR))

            if not cmds.objExists(right_joint):
                cmds.warning(f'[mixamo_rig_builder] mirror_proxy: joint {right_joint!r} not found — run Mirror Joints first.')
                continue

            # Delete existing right proxy if present
            if cmds.objExists(right_p):
                cmds.delete(right_p)

            # Duplicate left proxy, move to world space first so proxy_GRP transforms don't skew the mirror
            dup = cmds.duplicate(left_p, name='_mir_tmp_')[0]
            cmds.parent(dup, world=True)

            # Mirror in X by parenting to an empty group at world origin, scale X=-1
            mirror_grp = cmds.group(empty=True, name='_mirGrp_tmp_')
            cmds.parent(dup, mirror_grp)
            cmds.setAttr(mirror_grp + '.scaleX', -1)

            # Unparent back to world, freeze scale so transforms are clean
            cmds.parent(dup, world=True)
            cmds.makeIdentity(dup, apply=True, scale=True)
            cmds.delete(mirror_grp)

            # Update joint reference attribute (was copied as left joint name)
            cmds.setAttr(dup + '.' + PROXY_ATTR, right_joint, type='string')

            dup = cmds.rename(dup, right_p)
            cmds.parent(dup, PROXY_GRP)
            count += 1

        cmds.inViewMessage(
            assistMessage=f'<b>{count} proxy boxes mirrored</b> Left → Right. Select mesh and Skin.',
            position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] mirror_proxy failed: {e}')
    finally:
        cmds.undoInfo(closeChunk=True)


# ── Step 5: Skin ──────────────────────────────────────────────────────────────

def skin_mesh(blend_pct=0.10):
    """Bind selected mesh, assign weights from proxy boxes, smooth at boundaries, delete proxies."""
    sel = cmds.ls(selection=True, dag=True, type='mesh') or []
    if not sel:
        cmds.inViewMessage(assistMessage='<b>Select the character mesh</b> before skinning.',
                           position='topCenter', fade=True)
        return

    mesh = cmds.listRelatives(sel[0], parent=True)[0]
    joints = [j for j in JOINT_DATA if cmds.objExists(j)]
    if not joints:
        cmds.warning('[mixamo_rig_builder] No Mixamo joints found in scene.')
        return

    cmds.undoInfo(openChunk=True, chunkName='skin_mesh')
    try:
        # Bind skin
        skin = cmds.skinCluster(joints, mesh, toSelectedBones=True,
                                maximumInfluences=4, skinMethod=0, name='mixamo_skinCluster')[0]

        # Get all proxy boxes
        proxies = (cmds.listRelatives(PROXY_GRP, children=True, type='transform') or []) if cmds.objExists(PROXY_GRP) else []

        # Get all vertex world positions via API (fast)
        sel_list = om.MSelectionList()
        sel_list.add(mesh)
        dag_path = sel_list.getDagPath(0)
        fn_mesh  = om.MFnMesh(dag_path)
        points   = fn_mesh.getPoints(om.MSpace.kWorld)
        n_verts  = len(points)

        # Assign weights from each proxy box
        for proxy in proxies:
            if not cmds.attributeQuery(PROXY_ATTR, node=proxy, exists=True):
                continue
            joint = cmds.getAttr(proxy + '.' + PROXY_ATTR)
            if not cmds.objExists(joint):
                continue

            # Get proxy local bbox and world inverse matrix
            local_bb  = cmds.polyEvaluate(proxy, boundingBox=True)
            xmin, xmax = local_bb[0]
            ymin, ymax = local_bb[1]
            zmin, zmax = local_bb[2]

            mat     = cmds.xform(proxy, q=True, ws=True, matrix=True)
            inv_mat = om.MMatrix(mat).inverse()

            inside = []
            for i in range(n_verts):
                lp = om.MPoint(points[i]) * inv_mat
                if xmin <= lp.x <= xmax and ymin <= lp.y <= ymax and zmin <= lp.z <= zmax:
                    inside.append(i)

            for i in inside:
                cmds.skinPercent(skin, f'{mesh}.vtx[{i}]',
                                 transformValue=[(joint, 1.0)])

        # Smooth at bone boundaries
        _smooth_at_boundaries(mesh, skin, points, n_verts, blend_pct)

        # Delete proxy group
        if cmds.objExists(PROXY_GRP):
            cmds.delete(PROXY_GRP)

        cmds.inViewMessage(assistMessage='<b>Skinning complete.</b> Touch up left-side weights, then Mirror Skin.',
                           position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] skin_mesh failed: {e}')
    finally:
        cmds.undoInfo(closeChunk=True)


def _smooth_at_boundaries(mesh, skin, points, n_verts, blend_pct):
    """Gradient weight blend within blend_pct of each joint's position."""
    skinned = cmds.skinCluster(skin, q=True, influence=True) or []
    skinned_set = set(skinned)

    for joint in skinned:
        parent = cmds.listRelatives(joint, parent=True, type='joint')
        if not parent or parent[0] not in skinned_set:
            continue
        parent_joint = parent[0]

        children = cmds.listRelatives(joint, children=True, type='joint')
        if not children:
            continue

        j_pos   = om.MVector(*cmds.xform(joint, q=True, ws=True, t=True))
        c_pos   = om.MVector(*cmds.xform(children[0], q=True, ws=True, t=True))
        bone_len = (c_pos - j_pos).length()
        if bone_len < 0.001:
            continue
        blend_dist = bone_len * blend_pct

        for i in range(n_verts):
            p    = om.MVector(points[i].x, points[i].y, points[i].z)
            dist = (p - j_pos).length()
            if dist < blend_dist:
                t = dist / blend_dist          # 0 at joint → 1 at boundary
                w_parent = (1.0 - t) * 0.5    # max 50% at joint, 0 at boundary
                w_joint  = 1.0 - w_parent
                cmds.skinPercent(skin, f'{mesh}.vtx[{i}]',
                                 transformValue=[(parent_joint, w_parent),
                                                 (joint,        w_joint)])


# ── Step 6: Mirror Skin ───────────────────────────────────────────────────────

def mirror_skin():
    """Copy left-side skin weights to right using Maya's copySkinWeights."""
    sel = cmds.ls(selection=True, dag=True, type='mesh') or []
    if not sel:
        cmds.inViewMessage(assistMessage='<b>Select the character mesh</b> before mirroring skin.',
                           position='topCenter', fade=True)
        return

    mesh = cmds.listRelatives(sel[0], parent=True)[0]
    skin = _get_skin_cluster(mesh)
    if not skin:
        cmds.warning(f'[mixamo_rig_builder] No skinCluster found on {mesh}.')
        return

    cmds.undoInfo(openChunk=True, chunkName='mirror_skin')
    try:
        cmds.copySkinWeights(sourceSkin=skin, destinationSkin=skin,
                             mirrorMode='YZ', mirrorInverse=True,
                             surfaceAssociation='closestPoint',
                             influenceAssociation='closestJoint')
        cmds.inViewMessage(assistMessage='<b>Skin weights mirrored</b> Left → Right.',
                           position='topCenter', fade=True)
    except Exception as e:
        cmds.warning(f'[mixamo_rig_builder] mirror_skin failed: {e}')
    finally:
        cmds.undoInfo(closeChunk=True)


def _get_skin_cluster(mesh):
    history = cmds.listHistory(mesh) or []
    for node in history:
        if cmds.nodeType(node) == 'skinCluster':
            return node
    return None


# ── UI ────────────────────────────────────────────────────────────────────────

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class MixamoRigBuilderUI(QtWidgets.QDialog):
    def __init__(self, parent=_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(f'Mixamo Rig Builder  v{TOOL_VERSION}')
        self.setMinimumWidth(480)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Workflow note
        note = QtWidgets.QLabel(
            '  Workflow: Create Skeleton → scale mixamo_root_GRP to fit mesh → '
            'position LEFT joints → Mirror Joints → Create Proxy → '
            'fit LEFT proxies → Mirror Proxy → select mesh → Skin → Mirror Skin'
        )
        note.setWordWrap(True)
        note.setMinimumWidth(460)
        note.setStyleSheet('color:#e8a020; font-size:10px; background:#2a2a2a; padding:4px;')
        root.addWidget(note)

        # Step buttons
        steps = [
            ('1. Create Skeleton',  self._create_skeleton,  '#2980b9'),
            ('2. Mirror Joints',    self._mirror_joints,    '#8e44ad'),
            ('3. Create Proxy',     self._create_proxy,     '#27ae60'),
            ('4. Mirror Proxy',     self._mirror_proxy,     '#16a085'),
            ('5. Skin',             self._skin,             '#e67e22'),
            ('6. Mirror Skin',      self._mirror_skin,      '#c0392b'),
        ]
        btn_row = QtWidgets.QHBoxLayout()
        for label, slot, color in steps:
            btn = QtWidgets.QPushButton(label)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(f'background-color:{color}; color:white; font-weight:bold;')
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        root.addLayout(btn_row)

        # Helper: select root group for scaling
        helper_row = QtWidgets.QHBoxLayout()
        sel_root_btn = QtWidgets.QPushButton('Select Root Group (to scale skeleton)')
        sel_root_btn.setStyleSheet('background-color:#444; color:#ccc;')
        sel_root_btn.clicked.connect(self._select_root)
        helper_row.addWidget(sel_root_btn)
        root.addLayout(helper_row)

        # Settings
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet('color:#555;')
        root.addWidget(sep)

        settings_row = QtWidgets.QHBoxLayout()

        settings_row.addWidget(QtWidgets.QLabel('Proxy base size:'))
        self._proxy_size = QtWidgets.QDoubleSpinBox()
        self._proxy_size.setRange(1.0, 50.0)
        self._proxy_size.setValue(5.0)
        self._proxy_size.setSuffix(' units')
        self._proxy_size.setMinimumWidth(100)
        settings_row.addWidget(self._proxy_size)

        settings_row.addSpacing(20)
        settings_row.addWidget(QtWidgets.QLabel('Boundary blend:'))
        self._blend_pct = QtWidgets.QSpinBox()
        self._blend_pct.setRange(1, 30)
        self._blend_pct.setValue(10)
        self._blend_pct.setSuffix(' %')
        self._blend_pct.setMinimumWidth(70)
        settings_row.addWidget(self._blend_pct)
        settings_row.addStretch()
        root.addLayout(settings_row)

        # Status
        self._status = QtWidgets.QLabel('Ready — start with Create Skeleton.')
        self._status.setStyleSheet('color:#aaa; font-size:11px;')
        self._status.setMinimumWidth(460)
        root.addWidget(self._status)

    def _set_status(self, msg):
        self._status.setText(msg)

    def _select_root(self):
        if cmds.objExists(ROOT_GRP):
            cmds.select(ROOT_GRP)
            self._set_status(f'{ROOT_GRP} selected — scale it (R key) to fit your character mesh.')
        else:
            self._set_status('No root group yet — run Create Skeleton first.')

    def _create_skeleton(self):
        self._set_status('Creating skeleton…')
        create_skeleton()
        self._set_status('Skeleton created. Position left-side joints, then Mirror Joints.')

    def _mirror_joints(self):
        self._set_status('Mirroring joints…')
        mirror_joints()
        self._set_status('Joints mirrored. Now Create Proxy boxes.')

    def _create_proxy(self):
        self._set_status('Creating proxy boxes…')
        create_proxy_boxes(base_size=self._proxy_size.value())
        self._set_status('Proxies created. Adjust left-side boxes, then Mirror Proxy.')

    def _mirror_proxy(self):
        self._set_status('Mirroring proxy boxes…')
        mirror_proxy()
        self._set_status('Proxies mirrored. Select mesh and Skin.')

    def _skin(self):
        self._set_status('Skinning…')
        skin_mesh(blend_pct=self._blend_pct.value() / 100.0)
        self._set_status('Skinning done. Touch up weights, then Mirror Skin.')

    def _mirror_skin(self):
        self._set_status('Mirroring skin weights…')
        mirror_skin()
        self._set_status('Done! Skin weights mirrored Left → Right.')

    def closeEvent(self, event):
        self.deleteLater()
        super().closeEvent(event)


_tool_window = None


def show():
    """Entry point — called by shelf button."""
    global _tool_window
    try:
        _tool_window.close()
        _tool_window.deleteLater()
    except Exception:
        pass
    _tool_window = MixamoRigBuilderUI()
    _tool_window.show()


# ── Shelf installer ───────────────────────────────────────────────────────────

def _install_shelf_button():
    """Create or replace this tool's shelf button on the Pipeline shelf."""
    main_shelf = mel.eval('$gShelfTopLevel = $gShelfTopLevel')
    shelves = cmds.tabLayout(main_shelf, query=True, childArray=True) or []
    shelf = None
    for s in shelves:
        if s == SHELF_NAME:
            shelf = s
            break
    if shelf is None:
        shelf = cmds.shelfLayout(SHELF_NAME, parent=main_shelf)

    existing = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for btn in existing:
        try:
            if cmds.shelfButton(btn, query=True, label=True) == TOOL_LABEL:
                cmds.deleteUI(btn)
        except Exception:
            pass

    icon = TOOL_ICON
    if not os.path.isabs(icon) and not cmds.resourceString(icon):
        icon = os.path.join(_TOOL_DIR, icon)

    cmd = '\n'.join([
        'import sys, os',
        f"_p = r'{_TOOL_DIR}'",
        'if _p not in sys.path: sys.path.insert(0, _p)',
        f'import {TOOL_NAME}',
        f'import importlib; importlib.reload({TOOL_NAME})',
        f'{TOOL_NAME}.show()',
    ])

    cmds.shelfButton(parent=shelf, label=TOOL_LABEL, annotation=TOOL_DESCRIPTION,
                     command=cmd, image=icon, sourceType='python',
                     style='iconAndTextVertical')

    cmds.inViewMessage(
        assistMessage=f"<b>{TOOL_LABEL.replace(chr(10), ' ')}</b> added to <b>{SHELF_NAME}</b> shelf.",
        position='topCenter', fade=True)


def onMayaDroppedPythonFile(*args, **kwargs):
    """Maya calls this when the .py file is dragged into the viewport."""
    _install_shelf_button()

# ──────────────────────────────────────────────────────────────────────────────
