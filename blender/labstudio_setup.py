"""
Виртуално студио в стил „LABCOIN“ (шестоъгълници + лилав неон) за Blender 4.2+ / 5.x.

Как се ползва:
  1. Отвори Blender -> раздел Scripting -> Open -> този файл -> Run Script.
  2. Сложи до .blend файла:
       presenter.mp4  – твоето грийн скрийн видео (или PNG поредица с алфа)
       logo.svg       – логото за релефа на големия шестоъгълник (по желание;
                        без него се слага вградено лого-колба)
       screen.png     – снимка/видео на екрана на телефона (по желание)
     Ако ги няма, скриптът слага заместители, за да видиш сцената.
  3. Настройките са в блока НАСТРОЙКИ по-долу.

Скриптът изтрива всичко в текущата сцена и я сглобява наново.
"""

import bpy
import math
import os
import random
from mathutils import Vector

# ---------------------------------------------------------------- НАСТРОЙКИ
BASE_DIR = bpy.path.abspath("//") or os.path.dirname(os.path.abspath(__file__))

PLATE_FILE = os.path.join(BASE_DIR, "presenter.mp4")  # грийн скрийн видеото
PLATE_PREKEYED = False     # True, ако видеото вече е изрязано (PNG/ProRes с алфа)
PLATE_HEIGHT = 2.3         # височина на кадъра в метри (човекът да е ~1.8 m)
PLATE_FEET_OFFSET = 0.05   # колко е празното място под краката в кадъра (m)
KEY_THRESHOLD = 0.08       # от колко „зелено“ започва да се реже
KEY_SOFTNESS = 0.12        # мекота на ръба

PHONE_SCREEN_FILE = os.path.join(BASE_DIR, "screen.png")

ACCENT = (0.85, 0.18, 1.0)      # основен неон (лилаво); за „алармата“ -> (1, 0.05, 0.05)
ACTIVE_SET = "STUDIO"           # "STUDIO" или "CITY" (неоновият град/карта)
SHOW_PRESENTER = True           # False = празна сцена (без водещия)
SHOW_PROPS = True               # False = без балончетата и телефона
CEILING = True                  # таван с греди и лампи – да изглежда като затворена зала
FOG = True                      # лека мъгла -> сияние и лъчи като в оригинала (по-бавен рендер)

FPS = 25
DURATION_SEC = 30               # дължина на тестовата анимация; после я сменяш
ENGINE = "BLENDER_EEVEE"        # за финала; "CYCLES" е по-красиво, но много по-бавно
# ---------------------------------------------------------------------------

random.seed(7)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.cameras, bpy.data.lights, bpy.data.node_groups):
        for item in list(block):
            block.remove(item)


def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def link(obj, coll):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


# ---------------------------------------------------------------- материали

def accent_group():
    """Един общ цвят за целия неон – смениш го тук и всичко се пребоядисва
    (може и да се анимира: лилаво -> червено за частта с проблемите)."""
    group = bpy.data.node_groups.get("ACCENT")
    if group:
        return group
    group = bpy.data.node_groups.new("ACCENT", "ShaderNodeTree")
    group.interface.new_socket("Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = group.nodes.new("NodeGroupOutput")
    rgb = group.nodes.new("ShaderNodeRGB")
    rgb.name = "AccentColor"
    rgb.outputs[0].default_value = (*ACCENT, 1.0)
    group.links.new(rgb.outputs[0], out.inputs[0])
    return group


def mat_basic(name, color, roughness=0.4, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def mat_emission(name, color=None, strength=5.0, use_accent=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = strength
    if use_accent:
        grp = nt.nodes.new("ShaderNodeGroup")
        grp.node_tree = accent_group()
        nt.links.new(grp.outputs[0], emit.inputs["Color"])
    else:
        emit.inputs["Color"].default_value = (*color, 1.0)
    nt.links.new(emit.outputs[0], out.inputs["Surface"])
    return mat


def load_image(path):
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=True)
        if path.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm")):
            img.source = "MOVIE"
        return img
    return None


def placeholder_plate():
    """Зелен кадър със силует – само за да се види сцената без истинско видео."""
    w, h = 960, 540
    img = bpy.data.images.new("PLATE_PLACEHOLDER", w, h, alpha=False)
    px = [0.0] * (w * h * 4)
    cx = w // 2
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            yy = y / h  # 0 долу, 1 горе
            dx = abs(x - cx) / h
            head = (dx ** 2 + (yy - 0.82) ** 2) < 0.06 ** 2
            body = yy > 0.03 and yy < 0.75 and dx < (0.11 if yy > 0.45 else 0.07)
            if head or body:
                px[i:i + 4] = (0.08, 0.07, 0.07, 1.0)
            else:
                px[i:i + 4] = (0.05, 0.75, 0.15, 1.0)
    img.pixels = px
    return img


def mat_plate(img, prekeyed):
    """Шейдър с вграден chroma key + премахване на зеления отблясък (despill).
    Emission, за да остане осветлението от снимките, а не да се осветява наново."""
    mat = bpy.data.materials.new("PLATE")
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    nt = mat.node_tree
    nt.nodes.clear()
    n = nt.nodes.new
    out = n("ShaderNodeOutputMaterial")
    tex = n("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "CLIP"
    if img.source == "MOVIE":
        tex.image_user.frame_duration = img.frame_duration
        tex.image_user.use_auto_refresh = True

    sep = n("ShaderNodeSeparateColor")
    nt.links.new(tex.outputs["Color"], sep.inputs[0])
    max_rb = n("ShaderNodeMath"); max_rb.operation = "MAXIMUM"
    nt.links.new(sep.outputs[0], max_rb.inputs[0])
    nt.links.new(sep.outputs[2], max_rb.inputs[1])

    # despill: зеленото не може да е повече от max(R, B)
    green = n("ShaderNodeMath"); green.operation = "MINIMUM"
    nt.links.new(sep.outputs[1], green.inputs[0])
    nt.links.new(max_rb.outputs[0], green.inputs[1])
    comb = n("ShaderNodeCombineColor")
    nt.links.new(sep.outputs[0], comb.inputs[0])
    nt.links.new(green.outputs[0], comb.inputs[1])
    nt.links.new(sep.outputs[2], comb.inputs[2])

    emit = n("ShaderNodeEmission")
    nt.links.new(comb.outputs[0], emit.inputs["Color"])
    transp = n("ShaderNodeBsdfTransparent")
    mix = n("ShaderNodeMixShader")

    if prekeyed:
        nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    else:
        key = n("ShaderNodeMath"); key.operation = "SUBTRACT"  # колко „зелено“ е
        nt.links.new(sep.outputs[1], key.inputs[0])
        nt.links.new(max_rb.outputs[0], key.inputs[1])
        alpha = n("ShaderNodeMapRange")
        alpha.interpolation_type = "SMOOTHSTEP"
        alpha.inputs["From Min"].default_value = KEY_THRESHOLD
        alpha.inputs["From Max"].default_value = KEY_THRESHOLD + KEY_SOFTNESS
        alpha.inputs["To Min"].default_value = 1.0
        alpha.inputs["To Max"].default_value = 0.0
        nt.links.new(key.outputs[0], alpha.inputs["Value"])
        nt.links.new(alpha.outputs["Result"], mix.inputs["Fac"])

    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------- геометрия

def hex_prism(name, radius, depth, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def hex_ring(name, radius, thickness, loc, rot=(0, 0, 0), mat=None):
    """Неонов контур на шестоъгълник (тръба по ръба)."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = thickness
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(5)
    for i, p in enumerate(spline.points):
        a = math.radians(60 * i + 90)  # като върховете на primitive_cylinder
        p.co = (radius * math.cos(a), radius * math.sin(a), 0, 1)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        curve.materials.append(mat)
    return obj


def box(name, size, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    if mat:
        obj.data.materials.append(mat)
    return obj


def float_anim(obj, amp=0.06, period=4.0, phase=0.0):
    """Бавно „плаване“ нагоре-надолу, както иконите в оригинала."""
    base = obj.location.z
    frames = int(FPS * DURATION_SEC)
    step = int(FPS / 2)
    for f in range(1, frames + 1, step):
        obj.location.z = base + amp * math.sin(2 * math.pi * (f / FPS) / period + phase)
        obj.keyframe_insert("location", index=2, frame=f)
    obj.location.z = base


def pop_in(obj, frame, length=8):
    """Изскачане (scale 0 -> 1.1 -> 1) в даден кадър – за появата на нова вещ."""
    final = obj.scale.copy()
    obj.scale = (0, 0, 0)
    obj.keyframe_insert("scale", frame=frame)
    obj.scale = final * 1.1
    obj.keyframe_insert("scale", frame=frame + length)
    obj.scale = final
    obj.keyframe_insert("scale", frame=frame + length + 4)


# ---------------------------------------------------------------- части на сцената

# ---------------------------------------------------------------- детайлни материали

def _principled(mat):
    mat.use_nodes = True
    return mat.node_tree, mat.node_tree.nodes["Principled BSDF"]


def _marble_fac(nt, scale, distortion=5.0, seed=0.0):
    """Мраморни жилки: изкривен noise -> тясна ивица около 0.5."""
    n = nt.nodes.new
    coord = n("ShaderNodeTexCoord")
    mapping = n("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (seed, seed * 0.7, seed * 1.3)
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    noise = n("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.2
    noise.inputs["Detail"].default_value = 12
    noise.inputs["Roughness"].default_value = 0.62
    noise.inputs["Distortion"].default_value = distortion
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = n("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.47, (0, 0, 0, 1)
    els[1].position, els[1].color = 0.5, (1, 1, 1, 1)
    e = els.new(0.53)
    e.color = (0, 0, 0, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    return ramp.outputs["Color"], noise.outputs["Fac"]


def mat_marble(name, base, vein, roughness=0.25, emission=0.0, scale=0.6, seed=0.0):
    """Мрамор с жилки; emission > 0 -> мраморът свети (розовите ниши)."""
    mat = bpy.data.materials.new(name)
    nt, bsdf = _principled(mat)
    veins, cloud = _marble_fac(nt, scale, seed=seed)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*base, 1)
    mix.inputs[7].default_value = (*vein, 1)
    nt.links.new(veins, mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = roughness * 0.7
    rough.inputs["To Max"].default_value = roughness * 1.4
    nt.links.new(cloud, rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    if emission:
        nt.links.new(mix.outputs[2], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def mat_floor_tiles():
    """Тъмен лъскав камък, всяка плочка с малко различен тон,
    по някои плочки – светещи пукнатини (като долу вдясно в оригинала)."""
    mat = bpy.data.materials.new("FloorTiles")
    nt, bsdf = _principled(mat)
    n = nt.nodes.new
    veins, cloud = _marble_fac(nt, 0.35, distortion=7.0, seed=3.0)
    geo = n("ShaderNodeAttribute")
    geo.attribute_name = "tile_rand"
    tone = n("ShaderNodeMapRange")
    tone.inputs["To Min"].default_value = 0.65
    tone.inputs["To Max"].default_value = 1.25
    nt.links.new(geo.outputs["Fac"], tone.inputs["Value"])
    mix = n("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.02, 0.008, 0.032, 1)
    mix.inputs[7].default_value = (0.065, 0.03, 0.09, 1)
    nt.links.new(veins, mix.inputs["Factor"])
    tint = n("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    nt.links.new(mix.outputs[2], tint.inputs[6])
    comb = n("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(tone.outputs["Result"], comb.inputs[i])
    nt.links.new(comb.outputs[0], tint.inputs[7])
    nt.links.new(tint.outputs[2], bsdf.inputs["Base Color"])
    rough = n("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.08
    rough.inputs["To Max"].default_value = 0.3
    nt.links.new(cloud, rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Coat Weight"].default_value = 0.4
    bsdf.inputs["Coat Roughness"].default_value = 0.05

    # пукнатини: ръбове на voronoi, само по ~8% от плочките
    coord = n("ShaderNodeTexCoord")
    warp = n("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 3.0
    wmix = n("ShaderNodeMix")
    wmix.data_type = "VECTOR"
    wmix.inputs["Factor"].default_value = 0.08
    nt.links.new(coord.outputs["Object"], wmix.inputs[4])
    nt.links.new(warp.outputs["Color"], wmix.inputs[5])
    vor = n("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 2.2
    nt.links.new(wmix.outputs[1], vor.inputs["Vector"])
    crack = n("ShaderNodeMapRange")
    crack.inputs["From Min"].default_value = 0.0
    crack.inputs["From Max"].default_value = 0.012
    crack.inputs["To Min"].default_value = 1.0
    crack.inputs["To Max"].default_value = 0.0
    nt.links.new(vor.outputs["Distance"], crack.inputs["Value"])
    pick = n("ShaderNodeMath"); pick.operation = "GREATER_THAN"
    pick.inputs[1].default_value = 0.92
    nt.links.new(geo.outputs["Fac"], pick.inputs[0])
    mask = n("ShaderNodeMath"); mask.operation = "MULTIPLY"
    nt.links.new(crack.outputs["Result"], mask.inputs[0])
    nt.links.new(pick.outputs[0], mask.inputs[1])
    strength = n("ShaderNodeMath"); strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 6.0
    nt.links.new(mask.outputs[0], strength.inputs[0])
    grp = n("ShaderNodeGroup")
    grp.node_tree = accent_group()
    nt.links.new(grp.outputs[0], bsdf.inputs["Emission Color"])
    nt.links.new(strength.outputs[0], bsdf.inputs["Emission Strength"])
    return mat


def studio_materials():
    m = {}
    m["chrome"] = mat_basic("Chrome", (0.85, 0.8, 0.9), roughness=0.08, metallic=1.0)
    m["dark_metal"] = mat_basic("DarkMetal", (0.04, 0.02, 0.06), roughness=0.22, metallic=0.85)
    m["wall"] = mat_marble("WallDark", (0.035, 0.013, 0.055), (0.08, 0.035, 0.11),
                           roughness=0.3, scale=0.45, seed=1.0)
    m["pillar"] = mat_marble("PillarStone", (0.05, 0.02, 0.075), (0.16, 0.08, 0.2),
                             roughness=0.18, scale=0.8, seed=2.0)
    m["niche"] = mat_marble("NicheMarble", (0.42, 0.05, 0.58), (0.78, 0.3, 0.95),
                            roughness=0.35, emission=0.22, scale=0.5, seed=4.0)
    m["alcove"] = mat_basic("AlcoveBlack", (0.004, 0.003, 0.01), roughness=0.25, metallic=0.3)
    m["plaque"] = mat_marble("LogoPlaque", (0.72, 0.3, 0.88), (0.88, 0.58, 1.0),
                             roughness=0.45, emission=0.08, scale=0.9, seed=5.0)
    m["logo"] = mat_basic("LogoRelief", (0.5, 0.16, 0.7), roughness=0.35)
    m["logo"].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.5, 0.16, 0.7, 1)
    m["logo"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.1
    m["led"] = mat_emission("LED", use_accent=True, strength=8)
    m["led_white"] = mat_emission("LEDWhite", (1.0, 0.55, 1.0), strength=4)
    m["tile"] = mat_floor_tiles()
    m["grout"] = mat_basic("Grout", (0.005, 0.002, 0.008), roughness=0.6)
    return m


# ---------------------------------------------------------------- детайлна геометрия

def mesh_object(name, verts, faces, coll, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    if mat:
        me.materials.append(mat)
    return obj


def add_bevel(obj, width=0.01, segments=2):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return mod


def extrude_polys(name, polys, depth, coll, mat=None):
    """Плоски форми (x, z) изтеглени по -Y – за релефа на логото."""
    verts, faces = [], []
    for poly in polys:
        n0 = len(verts)
        k = len(poly)
        verts += [(x, 0, z) for x, z in poly] + [(x, -depth, z) for x, z in poly]
        faces.append(tuple(n0 + i for i in range(k))[::-1])
        faces.append(tuple(n0 + k + i for i in range(k)))
        for i in range(k):
            j = (i + 1) % k
            faces.append((n0 + i, n0 + j, n0 + k + j, n0 + k + i))
    return mesh_object(name, verts, faces, coll, mat)


def circle_pts(cx, cz, r, n=40, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n)]


def hex_pts(r, flat_top=True):
    off = 0 if flat_top else 30
    return [(r * math.cos(math.radians(60 * i + off)),
             r * math.sin(math.radians(60 * i + off))) for i in range(6)]


def hex_band(name, r_out, r_in, z, height, coll, mat):
    """Шестоъгълна лента (рамка) – за вградените светещи ивици в пиедестала."""
    o, i_ = hex_pts(r_out), hex_pts(r_in)
    verts = ([(x, y, z) for x, y in o] + [(x, y, z) for x, y in i_] +
             [(x, y, z + height) for x, y in o] + [(x, y, z + height) for x, y in i_])
    faces = []
    for k in range(6):
        j = (k + 1) % 6
        faces.append((12 + k, 12 + j, 18 + j, 18 + k))   # горе
        faces.append((k, 6 + k, 6 + j, j))               # долу
        faces.append((k, j, 12 + j, 12 + k))             # външна стена
        faces.append((6 + k, 18 + k, 18 + j, 6 + j))     # вътрешна стена
    return mesh_object(name, verts, faces, coll, mat)


def hex_slab(name, r, z, height, coll, mat):
    pts = hex_pts(r)
    verts = [(x, y, z) for x, y in pts] + [(x, y, z + height) for x, y in pts]
    faces = [tuple(range(5, -1, -1)), tuple(range(6, 12))]
    faces += [(k, (k + 1) % 6, 6 + (k + 1) % 6, 6 + k) for k in range(6)]
    return mesh_object(name, verts, faces, coll, mat)


def build_hex_floor(coll, m, radius=10.5, tile_r=0.55, gap=0.035, height=0.04):
    """Под от отделни шестоъгълни плочки с фуги (един обект, ~600 плочки)."""
    verts, faces = [], []
    step = tile_r + gap / math.sqrt(3)
    dx, dy = 1.5 * step, math.sqrt(3) * step
    cols = int(radius / dx) + 2
    rows = int(radius / dy) + 2
    corners = hex_pts(tile_r, True)
    for c in range(-cols, cols + 1):
        for r in range(-rows, rows + 1):
            x = c * dx
            y = r * dy + (dy / 2 if c % 2 else 0)
            if math.hypot(x, y) > radius:
                continue
            n0 = len(verts)
            verts += [(x + px, y + py, 0) for px, py in corners]
            verts += [(x + px, y + py, height) for px, py in corners]
            faces.append(tuple(n0 + 6 + k for k in range(6)))
            faces += [(n0 + k, n0 + (k + 1) % 6, n0 + 6 + (k + 1) % 6, n0 + 6 + k)
                      for k in range(6)]
    floor = mesh_object("FloorTiles", verts, faces, coll, m["tile"])
    attr = floor.data.attributes.new("tile_rand", "FLOAT", "FACE")
    rng = random.Random(11)
    vals = []
    for _ in range(len(faces) // 7):   # 7 стени на плочка
        v = rng.random()
        vals += [v] * 7
    attr.data.foreach_set("value", vals)
    add_bevel(floor, 0.008, 2)
    bpy.ops.mesh.primitive_plane_add(size=2 * radius + 2, location=(0, 0, 0.005))
    link(bpy.context.active_object, coll).data.materials.append(m["grout"])
    return height


def build_platform(coll, m, floor_top):
    """Пиедестал като в оригинала: нисък тъмен шестоъгълник, светеща външна
    рамка, широка розова лента и вътрешен шестоъгълен контур."""
    z = floor_top
    link(hex_slab("Platform_Base", 2.05, z, 0.05, coll, m["pillar"]), coll)
    hex_band("PlatformEdgeLED", 2.06, 1.98, z, 0.052, coll, m["led_white"])
    z += 0.05
    hex_slab("Platform_Top", 1.75, z, 0.06, coll, m["pillar"])
    hex_band("PlatformBandLED", 1.55, 1.38, z + 0.06, 0.004, coll, m["led"])
    hex_band("PlatformInnerLED", 0.86, 0.8, z + 0.06, 0.004, coll, m["led_white"])
    hex_band("PlatformTrim", 1.76, 1.72, z, 0.062, coll, m["chrome"])
    return z + 0.06


# --- стени: осмоъгълна зала, всяка стена е „сегмент“

ROOM_R = 7.0
WALL_H = 7.0


def _seg_frame(k):
    a = math.radians(45 * k)
    d = Vector((math.sin(a), math.cos(a), 0))      # навън (към стената)
    t = Vector((math.cos(a), -math.sin(a), 0))     # по стената, отляво надясно
    return d * ROOM_R, d, t, -a


def _seg_box(name, coll, mat, k, x, y, z, sx, sy, sz):
    """Кутия в локалните координати на сегмент k: x по стената, y навътре в нея."""
    c, d, t, rot = _seg_frame(k)
    pos = c + t * x + d * y + Vector((0, 0, z))
    return link(box(name, (sx, sy, sz), pos, (0, 0, rot), mat=mat), coll)


def _seg_rod(name, coll, mat, k, x, y, z0, z1, r=0.022):
    c, d, t, rot = _seg_frame(k)
    pos = c + t * x + d * y + Vector((0, 0, (z0 + z1) / 2))
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=z1 - z0, location=pos)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return link(obj, coll)


def build_wall_segment(coll, m, k, kind):
    w = 2 * ROOM_R * math.tan(math.radians(22.5))
    half = w / 2
    p = f"Seg{k}_"
    if kind == "alcove":
        ow, oh, depth = 3.9, 5.2, 1.6     # отвор на тъмната ниша зад логото
    else:
        ow, oh, depth = 3.0, 5.4, 1.1     # розовите мраморни ниши
    jamb = half - ow / 2
    # стена около отвора
    _seg_box(p + "JambL", coll, m["wall"], k, -half + jamb / 2, 0.2, WALL_H / 2, jamb, 0.4, WALL_H)
    _seg_box(p + "JambR", coll, m["wall"], k, half - jamb / 2, 0.2, WALL_H / 2, jamb, 0.4, WALL_H)
    _seg_box(p + "Header", coll, m["wall"], k, 0, 0.2, (oh + WALL_H) / 2, ow, 0.4, WALL_H - oh)
    # профили над отвора (стъпаловиден корниз)
    for i, (h, dy) in enumerate([(0.12, -0.06), (0.06, -0.12)]):
        _seg_box(p + f"Cornice{i}", coll, m["dark_metal"], k, 0, dy, oh + 0.2 + i * 0.14,
                 ow + 0.5 - i * 0.2, 0.12, h)
    # долен цокъл по цялата стена + светеща лента
    _seg_box(p + "Plinth", coll, m["dark_metal"], k, 0, -0.05, 0.12, w, 0.3, 0.24)
    _seg_box(p + "PlinthLED", coll, m["led"], k, 0, -0.205, 0.26, w - 0.9, 0.01, 0.025)
    # вътрешност на нишата
    inner = m["alcove"] if kind == "alcove" else m["niche"]
    _seg_box(p + "Back", coll, inner, k, 0, depth + 0.1, oh / 2, ow, 0.2, oh)
    _seg_box(p + "SideL", coll, inner, k, -ow / 2 - 0.05, depth / 2 + 0.2, oh / 2, 0.1, depth, oh)
    _seg_box(p + "SideR", coll, inner, k, ow / 2 + 0.05, depth / 2 + 0.2, oh / 2, 0.1, depth, oh)
    _seg_box(p + "Top", coll, inner, k, 0, depth / 2 + 0.2, oh + 0.05, ow, depth, 0.1)
    ledge = 0.35 if kind != "alcove" else 0.28
    _seg_box(p + "Ledge", coll, m["pillar"], k, 0, depth / 2 + 0.1, ledge / 2, ow, depth + 0.2, ledge)
    _seg_box(p + "LedgeLED", coll, m["led"], k, 0, -0.005, ledge - 0.03, ow - 0.1, 0.012, 0.03)
    # хромирани лайстни отстрани на отвора (по две)
    for side in (-1, 1):
        for j, off in enumerate((0.03, 0.14)):
            _seg_rod(p + f"Rod{side}{j}", coll, m["chrome"], k, side * (ow / 2 + off), -0.02,
                     ledge, oh + 0.1)
    _seg_box(p + "TopTrim", coll, m["chrome"], k, 0, -0.02, oh + 0.06, ow + 0.3, 0.03, 0.03)

    if kind == "alcove":
        # тъмната ниша: тънка розова светлина по долния ръб и отразяващ под
        _seg_box(p + "AlcoveLED", coll, m["led"], k, 0, 0.3, ledge + 0.01, ow - 0.2, 0.04, 0.02)
    else:
        # светещи вертикални ръбове вътре в нишата + светлина, която я осветява
        for side in (-1, 1):
            _seg_box(p + f"EdgeLight{side}", coll, m["led_white"], k, side * (ow / 2 - 0.03), 0.25,
                     ledge + (oh - ledge) / 2, 0.03, 0.03, oh - ledge - 0.1)
        c, d, t, rot = _seg_frame(k)
        data = bpy.data.lights.new(p + "NicheLight", "AREA")
        data.shape = "RECTANGLE"
        data.size, data.size_y = ow * 0.9, oh * 0.8
        data.energy = 180
        data.color = (1.0, 0.3, 0.95)
        light = bpy.data.objects.new(p + "NicheLight", data)
        coll.objects.link(light)
        light.location = c + d * 0.35 + Vector((0, 0, oh / 2 + 0.2))
        light.rotation_euler = (d).to_track_quat("-Z", "Y").to_euler()  # свети навътре


def build_pillar(coll, m, k):
    """Колона в ъгъла между два сегмента: камък, хромирани ленти, база и капител."""
    a = math.radians(45 * k + 22.5)
    r = ROOM_R / math.cos(math.radians(22.5)) - 0.1
    pos = Vector((math.sin(a) * r, math.cos(a) * r, 0))
    rot = (0, 0, -a)
    inward = -Vector((math.sin(a), math.cos(a), 0))
    side = Vector((math.cos(a), -math.sin(a), 0))
    p = f"Pillar{k}_"
    link(box(p + "Shaft", (0.9, 0.9, WALL_H), pos + Vector((0, 0, WALL_H / 2)), rot, m["pillar"]), coll)
    link(box(p + "Base", (1.15, 1.15, 0.45), pos + Vector((0, 0, 0.225)), rot, m["dark_metal"]), coll)
    link(box(p + "Base2", (1.02, 1.02, 0.15), pos + Vector((0, 0, 0.52)), rot, m["chrome"]), coll)
    link(box(p + "Cap", (1.15, 1.15, 0.35), pos + Vector((0, 0, WALL_H - 0.6)), rot, m["dark_metal"]), coll)
    # вертикални хромирани ленти и светещ процеп по средата на лицето
    for s in (-0.3, 0.3):
        q = pos + inward * 0.46 + side * s
        link(box(p + f"Strip{s}", (0.04, 0.03, WALL_H - 1.4), q + Vector((0, 0, WALL_H / 2 - 0.05)),
                 rot, m["chrome"]), coll)
    q = pos + inward * 0.455
    link(box(p + "Slot", (0.05, 0.02, WALL_H - 1.6), q + Vector((0, 0, WALL_H / 2 - 0.05)), rot,
             m["led"]), coll)


def build_logo_plaque(coll, m, floor_top):
    """Голям релефен шестоъгълник с логото (колба с мехурчета) пред тъмната ниша.
    Ако има logo.svg до .blend файла – използва него вместо вграденото лого."""
    y, z, r, depth = ROOM_R - 0.75, 3.15, 1.55, 0.36
    plaque = hex_prism("LogoPlaque", r, depth, (0, y, z), (math.radians(90), math.radians(30), 0),
                       mat=m["plaque"])
    add_bevel(plaque, 0.07, 4)
    link(plaque, coll)
    rim = hex_prism("LogoPlaqueRim", r + 0.08, 0.12, (0, y + 0.18, z),
                    (math.radians(90), math.radians(30), 0), mat=m["led"])
    link(rim, coll)  # розово сияние зад ръба

    front = y - depth / 2
    svg = os.path.join(BASE_DIR, "logo.svg")
    if os.path.exists(svg) and _import_svg_logo(svg, coll, m, front, z, r):
        return
    # вградено лого: отворен кръг (колбата), течност-триъгълник и 3 мехурчета
    ring = (circle_pts(0.08, -0.2, 0.92, 48, math.radians(118), math.radians(118 + 300)) +
            circle_pts(0.08, -0.2, 0.7, 48, math.radians(118 + 300), math.radians(118)))
    liquid = [(-0.48, -0.72), (0.64, -0.72), (0.08, 0.12)]
    bubbles = [circle_pts(-0.62, 0.78, 0.2), circle_pts(-0.25, 1.05, 0.13),
               circle_pts(-0.62, 1.18, 0.09)]
    for name, polys in (("LogoRing", [ring]), ("LogoLiquid", [liquid]),
                        ("LogoBubbles", bubbles)):
        obj = extrude_polys(name, polys, 0.07, coll, m["logo"])
        obj.location = (0, front, z)
        add_bevel(obj, 0.015, 3)


def _import_svg_logo(path, coll, m, front, z, r):
    try:
        before = set(bpy.data.objects)
        bpy.ops.import_curve.svg(filepath=path)
        new = [o for o in bpy.data.objects if o not in before and o.type == "CURVE"]
        if not new:
            return False
        for o in new:
            o.data.materials.clear()
            o.data.materials.append(m["logo"])
            link(o, coll)
        # мащаб и позиция: логото да запълни ~65% от шестоъгълника
        bpy.context.view_layer.update()
        xs = [(o.matrix_world @ Vector(c)).x for o in new for c in o.bound_box]
        ys = [(o.matrix_world @ Vector(c)).y for o in new for c in o.bound_box]
        size = max(max(xs) - min(xs), max(ys) - min(ys)) or 1
        s = (r * 1.3) / size
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        pivot = bpy.data.objects.new("LogoSVG", None)
        coll.objects.link(pivot)
        for o in new:
            o.location.x -= cx
            o.location.y -= cy
            o.parent = pivot
        for o in new:
            o.data.extrude = 0.035 / s
        pivot.scale = (s, s, s)
        pivot.rotation_euler = (math.radians(90), 0, 0)
        pivot.location = (0, front - 0.02, z)
        return True
    except Exception as err:
        print("logo.svg не се зареди:", err)
        return False


def build_room(coll, m, floor_top):
    for k in range(8):
        build_wall_segment(coll, m, k, "alcove" if k == 0 else "niche")
        build_pillar(coll, m, k)
    build_logo_plaque(coll, m, floor_top)
    # светлина за логото и мек кръг светлина около пиедестала
    for name, loc, look, power, color, size in (
            ("LogoKey", (0, ROOM_R - 3.2, 4.6), (0, ROOM_R - 0.7, 3.1), 250, (1, 0.6, 1), 2.0),
            ("FloorPool", (0, 0, WALL_H - 0.4), (0, 0, 0), 300, (1, 0.5, 1), 3.0)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.size = power, color, size
        obj = bpy.data.objects.new(name, data)
        coll.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def build_ceiling(coll, m):
    """Таван: тъмна плоча, греди към колоните, кръг от лампи над пиедестала."""
    h = WALL_H
    bpy.ops.mesh.primitive_plane_add(size=2 * ROOM_R + 4, location=(0, 0, h))
    link(bpy.context.active_object, coll).data.materials.append(m["wall"])
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        length = ROOM_R / math.cos(math.radians(22.5)) - 3.0
        mid = Vector((math.sin(a), math.cos(a), 0)) * (3.0 + length / 2)
        link(box(f"Beam_{k}", (0.4, length, 0.45), (mid.x, mid.y, h - 0.22), (0, 0, -a),
                 m["dark_metal"]), coll)
        link(box(f"BeamLED_{k}", (0.05, length - 0.3, 0.01), (mid.x, mid.y, h - 0.455), (0, 0, -a),
                 m["led"]), coll)
    hex_band("CeilingRing", 3.1, 2.8, h - 0.6, 0.18, coll, m["dark_metal"])
    hex_band("CeilingRingLED", 2.95, 2.88, h - 0.61, 0.01, coll, m["led_white"])
    for i in range(12):
        a = math.radians(30 * i)
        pos = Vector((math.cos(a) * 2.95, math.sin(a) * 2.95, h - 0.66))
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.11, depth=0.1, location=pos)
        link(bpy.context.active_object, coll).data.materials.append(m["led_white"])
        data = bpy.data.lights.new(f"Spot_{i}", "SPOT")
        data.energy = 60
        data.color = (1.0, 0.6, 1.0)
        data.spot_size = math.radians(28)
        data.spot_blend = 0.5
        spot = bpy.data.objects.new(f"Spot_{i}", data)
        coll.objects.link(spot)
        spot.location = pos - Vector((0, 0, 0.08))
        spot.rotation_euler = (Vector((0, 0, 0.2)) - spot.location).to_track_quat("-Z", "Y").to_euler()

    if FOG:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h / 2))
        fog = link(bpy.context.active_object, coll)
        fog.name = "Fog"
        fog.scale = (2 * ROOM_R - 0.6, 2 * ROOM_R - 0.6, h - 0.1)
        mat = bpy.data.materials.new("Fog")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = 0.018
        vol.inputs["Color"].default_value = (1.0, 0.8, 1.0, 1)
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
        fog.data.materials.append(mat)


def build_bubbles(coll):
    """Цветните шестоъгълни „балончета“, които се появяват около водещия."""
    colors = [(0.2, 0.45, 1.0), (1.0, 0.45, 0.05), (0.55, 0.15, 1.0),
              (0.95, 0.9, 1.0), (1.0, 0.7, 0.05)]
    spots = [(-1.3, 0.6, 2.9), (-0.45, 0.8, 3.35), (0.5, 0.8, 3.35),
             (-1.5, 0.6, 2.1), (1.35, 0.6, 2.3)]
    for i, (col, loc) in enumerate(zip(colors, spots)):
        obj = hex_prism(f"Bubble_{i}", 0.36, 0.08, loc, (math.radians(90), 0, 0),
                        mat=mat_emission(f"Bubble_{i}", col, strength=2.0))
        bpy.ops.object.modifier_add(type="BEVEL")
        obj.modifiers["Bevel"].width = 0.02
        obj.modifiers["Bevel"].segments = 3
        link(obj, coll)
        float_anim(obj, phase=i)
        pop_in(obj, frame=FPS * 2 + i * 6)


def build_phone(coll):
    """Плаващ телефон с екран (картинка или видео на приложението)."""
    body = mat_basic("PhoneBody", (0.01, 0.01, 0.012), roughness=0.15, metallic=0.9)
    phone = box("Phone", (0.72, 0.05, 1.48), (-1.75, 0.3, 2.0), mat=body)
    bev = phone.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.09
    bev.segments = 8
    link(phone, coll)

    screen_img = load_image(PHONE_SCREEN_FILE)
    if screen_img:
        mat = bpy.data.materials.new("PhoneScreen")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = screen_img
        if screen_img.source == "MOVIE":
            tex.image_user.frame_duration = screen_img.frame_duration
            tex.image_user.use_auto_refresh = True
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs["Strength"].default_value = 1.5
        nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
        nt.links.new(emit.outputs[0], out.inputs["Surface"])
    else:
        mat = mat_emission("PhoneScreen", (0.15, 0.05, 0.25), strength=1.5)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.51, 0),
                                     rotation=(math.radians(90), 0, 0))
    screen = bpy.context.active_object
    screen.name = "PhoneScreen"
    screen.scale = (0.9, 0.93, 1)
    screen.data.materials.append(mat)
    screen.parent = phone
    link(screen, coll)

    phone.rotation_euler = (0, 0, math.radians(18))
    float_anim(phone, amp=0.05, period=5)
    pop_in(phone, frame=FPS * 4)


def build_city(coll, neon):
    """Неоновият „град/карта“ – водещият стои на платформа над светеща мрежа."""
    dark = mat_basic("CityBlock", (0.06, 0.01, 0.09), roughness=0.5)
    edge = mat_emission("CityEdge", use_accent=True, strength=4)
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -4.0))
    ground = link(bpy.context.active_object, coll)
    ground.data.materials.append(mat_emission("CityGround", (0.25, 0.03, 0.35), strength=0.4))
    for gx in range(-14, 15):
        for gy in range(-8, 20):
            if random.random() < 0.25:
                continue  # „улици“
            h = random.uniform(0.3, 2.5)
            blk = box(f"Block_{gx}_{gy}", (1.6, 1.6, h),
                      (gx * 2.0, gy * 2.0, -4.0 + h / 2), mat=dark)
            link(blk, coll)
    # общ обект за ръбовете (wireframe) – по-бързо от отделни
    blocks = [o for o in coll.objects if o.name.startswith("Block_")]
    bpy.ops.object.select_all(action="DESELECT")
    for o in blocks:
        o.select_set(True)
    bpy.context.view_layer.objects.active = blocks[0]
    bpy.ops.object.join()
    city = bpy.context.active_object
    city.name = "CityBlocks"
    edges = city.copy()
    edges.data = city.data.copy()
    edges.name = "CityEdges"
    coll.objects.link(edges)
    edges.data.materials.clear()
    edges.data.materials.append(edge)
    wire = edges.modifiers.new("Wire", "WIREFRAME")
    wire.thickness = 0.03


def build_plate(top_z):
    img = load_image(PLATE_FILE) or placeholder_plate()
    w, h = img.size if img.size[0] else (1920, 1080)
    aspect = w / h
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0),
                                     rotation=(math.radians(90), 0, 0))
    plate = bpy.context.active_object
    plate.name = "PRESENTER"
    plate.scale = (PLATE_HEIGHT * aspect, PLATE_HEIGHT, 1)
    plate.location = (0, 0, top_z + PLATE_HEIGHT / 2 - PLATE_FEET_OFFSET)
    plate.data.materials.append(mat_plate(img, PLATE_PREKEYED))
    link(plate, collection("PRESENTER"))
    return plate


def build_cameras():
    """Три камери като в оригинала: общ, среден и близък план.
    Всяка прави бавно „приближаване“ (dolly), за да не е статичен кадърът."""
    cams = {}
    setups = {
        # име: (lens, старт, край, точка на гледане)
        # като кадъра от оригинала: леко отгоре, логото над главата
        "CAM_REF": (28, (0, -5.6, 2.05), (0, -5.3, 2.05), (0, 1.5, 1.6)),
        "CAM_WIDE": (16, (0, -6.3, 2.5), (0, -5.8, 2.4), (0, 0, 2.2)),
        "CAM_MEDIUM": (40, (0.5, -5.0, 1.6), (0.3, -4.6, 1.6), (0, 0, 1.45)),
        "CAM_CLOSE": (85, (0.8, -4.6, 1.75), (0.7, -4.3, 1.75), (0.3, 0, 1.7)),
        # кадри „отвътре“ за празното студио
        "CAM_LOW": (16, (0.4, -3.8, 0.3), (0.0, -3.4, 0.3), (0, 4, 3.4)),
        "CAM_SIDE": (20, (4.6, -3.8, 2.0), (4.0, -4.3, 2.0), (-1.0, 2.5, 2.4)),
        "CAM_HIGH": (16, (-4.5, -5.0, 5.5), (-4.0, -5.3, 5.4), (0, 1.0, 1.0)),
    }
    end = FPS * DURATION_SEC
    for name, (lens, start, finish, look) in setups.items():
        data = bpy.data.cameras.new(name)
        data.lens = lens
        cam = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(cam)
        aim = bpy.data.objects.new(name + "_AIM", None)
        bpy.context.scene.collection.objects.link(aim)
        aim.location = look
        track = cam.constraints.new("TRACK_TO")
        track.target = aim
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"
        cam.location = start
        cam.keyframe_insert("location", frame=1)
        cam.location = finish
        cam.keyframe_insert("location", frame=end)
        cams[name] = cam
    # смяна на камерите с маркери (Ctrl+B в Timeline за още)
    scene = bpy.context.scene
    order = ["CAM_WIDE", "CAM_MEDIUM", "CAM_CLOSE", "CAM_WIDE"]
    for i, name in enumerate(order):
        m = scene.timeline_markers.new(name, frame=1 + i * (end // len(order)))
        m.camera = cams[name]
    scene.camera = cams["CAM_WIDE"]
    return cams


def build_lights(coll):
    def area(name, loc, color, power, size, look=(0, 0, 1.5)):
        data = bpy.data.lights.new(name, "AREA")
        data.color = color
        data.energy = power
        data.size = size
        obj = bpy.data.objects.new(name, data)
        coll.objects.link(obj)
        obj.location = loc
        direction = Vector(look) - Vector(loc)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    # светлините трябва да съвпадат с тези на снимките (лилав контур отстрани)
    area("Rim_L", (-3.5, 2.5, 3.5), ACCENT, 600, 1.5)
    area("Rim_R", (3.5, 2.5, 3.5), ACCENT, 600, 1.5)
    area("Fill_Front", (0, -6, 5), (1.0, 0.8, 1.0), 300, 4)


def setup_world_and_render():
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = FPS * DURATION_SEC
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.004, 0.001, 0.008, 1)
    bg.inputs["Strength"].default_value = 1.0

    try:
        scene.render.engine = ENGINE
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    if hasattr(scene, "eevee"):
        ee = scene.eevee
        for attr, val in (("use_raytracing", True), ("use_shadows", True),
                          ("taa_render_samples", 64)):
            if hasattr(ee, attr):
                setattr(ee, attr, val)
    # Standard пази наситеното маджента (AgX/Filmic го избелват към лилаво-бяло)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"

    # bloom (сиянието около неона) през композитора
    try:
        if hasattr(scene, "compositing_node_group"):  # Blender 5.x
            tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
            scene.compositing_node_group = tree
            tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            out = tree.nodes.new("NodeGroupOutput")
        else:  # Blender 4.x
            scene.use_nodes = True
            tree = scene.node_tree
            tree.nodes.clear()
            out = tree.nodes.new("CompositorNodeComposite")
        rl = tree.nodes.new("CompositorNodeRLayers")
        glare = tree.nodes.new("CompositorNodeGlare")
        if "Type" in glare.inputs:  # 5.x: настройките са входове
            glare.inputs["Type"].default_value = "Bloom"
            glare.inputs["Threshold"].default_value = 0.8
            glare.inputs["Strength"].default_value = 0.6
            glare.inputs["Size"].default_value = 0.6
        else:
            glare.glare_type = "BLOOM"
            glare.threshold = 0.8
            glare.mix = -0.4
            glare.size = 8
        tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
        tree.links.new(glare.outputs["Image"], out.inputs[0])
    except Exception as err:  # bloom не е задължителен
        print("Bloom не е настроен:", err)


def main():
    clear_scene()
    neon = mat_emission("Neon", use_accent=True, strength=4)

    studio = collection("STUDIO")
    city = collection("CITY")
    props = collection("PROPS")
    lights = collection("LIGHTS")

    m = studio_materials()
    floor_top = build_hex_floor(studio, m)
    top_z = build_platform(studio, m, floor_top)
    build_room(studio, m, floor_top)
    if CEILING:
        build_ceiling(studio, m)

    city_platform = collection("CITY_PLATFORM")
    city.children.link(city_platform)
    bpy.context.scene.collection.children.unlink(city_platform)
    build_city(city, neon)
    for obj in [o for o in studio.objects if o.name.startswith("Platform")]:
        dup = obj.copy()
        city_platform.objects.link(dup)

    build_bubbles(props)
    build_phone(props)
    build_lights(lights)

    build_plate(top_z)
    build_cameras()
    setup_world_and_render()

    # показваме само избрания декор
    layers = bpy.context.view_layer.layer_collection.children
    layers["STUDIO"].exclude = ACTIVE_SET != "STUDIO"
    layers["CITY"].exclude = ACTIVE_SET != "CITY"
    layers["PRESENTER"].exclude = not SHOW_PRESENTER
    layers["PROPS"].exclude = not SHOW_PROPS
    bpy.context.scene.frame_set(1)
    print("Готово: студиото е сглобено.")


main()
