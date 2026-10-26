"""
Виртуално студио в стил „LABCOIN“ (шестоъгълници + лилав неон) за Blender 4.2+ / 5.x.

Как се ползва:
  1. Отвори Blender -> раздел Scripting -> Open -> този файл -> Run Script.
  2. Сложи до .blend файла:
       presenter.mp4  – твоето грийн скрийн видео (или PNG поредица с алфа)
       logo.png       – логото за големия шестоъгълник (по желание)
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

LOGO_FILE = os.path.join(BASE_DIR, "logo.png")
PHONE_SCREEN_FILE = os.path.join(BASE_DIR, "screen.png")

ACCENT = (0.85, 0.18, 1.0)      # основен неон (лилаво); за „алармата“ -> (1, 0.05, 0.05)
BACKDROP = (1.0, 0.62, 0.98)    # светлият розов шестоъгълник отзад
ACTIVE_SET = "STUDIO"           # "STUDIO" или "CITY" (неоновият град/карта)

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

def build_platform(coll, neon):
    dark = mat_basic("PlatformDark", (0.03, 0.015, 0.05), roughness=0.25, metallic=0.6)
    top = 0.0
    for i, (r, h) in enumerate([(1.7, 0.10), (1.45, 0.10), (1.2, 0.10)]):
        z = top + h / 2
        link(hex_prism(f"Platform_{i}", r, h, (0, 0, z), mat=dark), coll)
        link(hex_ring(f"PlatformNeon_{i}", r, 0.012, (0, 0, top + h), mat=neon), coll)
        top += h
    return top  # височината, на която стъпва водещият


def build_floor(coll, neon):
    floor = mat_basic("Floor", (0.012, 0.006, 0.02), roughness=0.12, metallic=0.3)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    link(bpy.context.active_object, coll).data.materials.append(floor)
    # неонови линии по пода, които излизат от платформата
    for i in range(6):
        a = math.radians(60 * i + 30)
        length = 6.0
        c = Vector((math.cos(a), math.sin(a), 0)) * (1.7 + length / 2)
        link(box(f"FloorLine_{i}", (length, 0.03, 0.005), (c.x, c.y, 0.003),
                 (0, 0, a), mat=neon), coll)


def build_backdrop(coll, neon):
    bright = mat_emission("BackdropHex", BACKDROP, strength=2.5)
    frame = mat_basic("BackdropFrame", (0.08, 0.03, 0.12), roughness=0.3)
    y, z = 4.5, 3.3
    link(hex_prism("BackdropFrame", 2.55, 0.25, (0, y + 0.1, z),
                   (math.radians(90), 0, 0), mat=frame), coll)
    link(hex_prism("BackdropHex", 2.3, 0.3, (0, y, z),
                   (math.radians(90), 0, 0), mat=bright), coll)
    link(hex_ring("BackdropNeon", 2.55, 0.02, (0, y - 0.16, z),
                  (math.radians(90), 0, 0), mat=neon), coll)

    logo = load_image(LOGO_FILE)
    if logo:
        mat = bpy.data.materials.new("Logo")
        mat.use_nodes = True
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = logo
        bsdf = nt.nodes["Principled BSDF"]
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, y - 0.17, z),
                                         rotation=(math.radians(90), 0, 0))
        link(bpy.context.active_object, coll).data.materials.append(mat)


def build_pillars(coll, neon):
    """Колони в полукръг с вертикални светещи панели + тъмни стени между тях."""
    dark = mat_basic("PillarDark", (0.025, 0.01, 0.04), roughness=0.35, metallic=0.4)
    panel = mat_emission("PillarLight", use_accent=True, strength=3)
    wall = mat_basic("Wall", (0.05, 0.015, 0.08), roughness=0.6)
    radius = 7.5
    angles = [-80, -58, -36, -14, 14, 36, 58, 80]
    for i, deg in enumerate(angles):
        a = math.radians(deg)
        pos = Vector((math.sin(a) * radius, math.cos(a) * radius, 3.0))
        rot = (0, 0, -a)
        link(box(f"Pillar_{i}", (0.7, 0.7, 6.0), pos, rot, mat=dark), coll)
        front = pos - Vector((math.sin(a), math.cos(a), 0)) * 0.36
        link(box(f"PillarLight_{i}", (0.35, 0.02, 4.6), front, rot, mat=panel), coll)
    for i in range(len(angles) - 1):
        a = math.radians((angles[i] + angles[i + 1]) / 2)
        pos = Vector((math.sin(a) * (radius + 0.4), math.cos(a) * (radius + 0.4), 3.0))
        link(box(f"Wall_{i}", (2.9, 0.15, 6.0), pos, (0, 0, -a), mat=wall), coll)


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
    return plate


def build_cameras():
    """Три камери като в оригинала: общ, среден и близък план.
    Всяка прави бавно „приближаване“ (dolly), за да не е статичен кадърът."""
    cams = {}
    setups = {
        # име: (lens, старт, край, точка на гледане)
        "CAM_WIDE": (24, (0, -10.5, 1.7), (0, -9.0, 1.9), (0, 0, 1.8)),
        "CAM_MEDIUM": (45, (0.6, -6.2, 1.55), (0.3, -5.6, 1.6), (0, 0, 1.45)),
        "CAM_CLOSE": (85, (0.9, -5.6, 1.75), (0.75, -5.2, 1.75), (0.35, 0, 1.75)),
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
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items_static
    ] else "None"

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

    top_z = build_platform(studio, neon)
    build_floor(studio, neon)
    build_backdrop(studio, neon)
    build_pillars(studio, neon)

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
    bpy.context.scene.frame_set(1)
    print("Готово: студиото е сглобено.")


main()
