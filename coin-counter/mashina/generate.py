"""Монетомат: машина с ръчка за монети от 50 евроцента – генератор на STL и 3MF файлове.

Как работи:
  1. Изсипваш монетите в бункера (наклонен на 45°, побира ~400–500 монети).
  2. Въртиш дръжката. Дискът има 8 гнезда; всяко загребва по 1 монета от купа, изкачва я
     горе и я пуска през дупка в задната плоча. Монетите се нареждат една върху друга в тръба.
  3. Две бутала на дъното на тръбата:
       лявото бутало (буташ надясно)  -> ТОЧНО 10 монети = 5 €  -> дясната чашка
       предното бутало (буташ навътре) -> ТОЧНО 20 монети = 10 € -> задната чашка
     Изходът е висок 10,5 (или 20,5) монети – следващата монета се опира в ръба и остава.

Нужни са още: болт M8×65 + шайба M8 + самоконтрираща гайка M8 (оста на диска).

Стартиране:  pip install manifold3d trimesh numpy  &&  python3 generate.py
Всички размери са в милиметри. Световни координати: X надясно, Y навътре (от теб), Z нагоре.
"""
import base64
import io
import json
import math
import os
import uuid
import zipfile

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

# ---- Монета 50 евроцента ----
COIN_D = 24.25
COIN_T = 2.38

# ---- Дозатор ----
COINS_A = 10                 # лявото бутало: 10 монети = 5 €
COINS_B = 20                 # предното бутало: 20 монети = 10 €


def gate(n):
    """Височина на изхода: n + половин монета – следващата монета се закача за ръба."""
    return (n + 0.5) * COIN_T


def push_h(n):
    """Височина на канала за буталото: n − половин монета – не докосва монета n+1."""
    return (n - 0.5) * COIN_T


BORE_R = 12.75               # радиус на тръбата (монета + 1,25 мм хлабина)
FLOOR_Z = 45.0               # височина на дъното на тръбата (под него стоят чашките)
BLOCK_TOP = FLOOR_Z + gate(COINS_B) + 15
STROKE = 30.0                # ход на буталата
PUSHER_LEN = 34.0
ROD_LEN = 48.0
RETRACT = 15.0               # прибраното бутало е на 15 мм от оста на тръбата
CUP_OFF = 35.0               # чашките: на 35 мм от оста (частично под ръба на изхода)

# ---- Бункер и диск ----
TILT = 45.0
C_Z = 185.0                  # височина на центъра на диска
PLATE_T = 6.0
PLATE_X = 80.0               # половин ширина на плочата
PLATE_B = (-95.0, 100.0)     # плочата по наклона (надолу, нагоре)
DISC_R = 70.0
DISC_T = 2.2                 # малко по-тънък от монетата – в гнездото влиза само 1 монета
POCKETS = 8
POCKET_R = 48.0
POCKET_D = COIN_D + 1.15
EXIT_D = 27.0
RING_ID = 2 * DISC_R + 3     # 1,5 мм около диска – по-малко от дебелината на монета
RING_H = 90.0
BOLT_D = 8.6
CHEEK_X = 74.0               # страничните стени са от CHEEK_X до PLATE_X

S = math.sqrt(0.5)
MAG_Y = round((POCKET_R + PLATE_T) * S) + 3   # оста на тръбата – малко зад дупката в плочата
CUP_A = (CUP_OFF, MAG_Y - 8)                  # чашка 5 € (вдясно), изместена напред, за да не опира в другата
CUP_B = (-8, MAG_Y + CUP_OFF)                 # чашка 10 € (отзад), изместена наляво
FUNNEL_Z = C_Z - 15

SEG = 96
HERE = os.path.dirname(os.path.abspath(__file__))
BED = 256.0                  # Bambu Lab A1


def cyl(h, r, r2=None, center=False):
    return Manifold.cylinder(h, r, r if r2 is None else r2, circular_segments=SEG, center=center)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def to_world(m):
    """От координатите на плочата (център на диска в 0, Z = нормалата на плочата) към света."""
    return m.rotate([TILT, 0, 0]).translate([0, 0, C_Z])


def plate_underside_z(y):
    return C_Z + y - PLATE_T / S


# ------------------------------------------------------------------ части
def make_base():
    """Основа: дозатор с две бутала + две странични стени, на които лежи бункерът."""
    ga, gb = gate(COINS_A), gate(COINS_B)
    pa, pb = push_h(COINS_A), push_h(COINS_B)
    za, zb = FLOOR_Z + pa / 2, FLOOR_Z + pb / 2
    wall_a = -(RETRACT + PUSHER_LEN)          # вътрешната стена зад прибраното бутало

    blk = box(wall_a - 6, 18, MAG_Y + wall_a - 6, MAG_Y + 18, 0, BLOCK_TOP)
    blk -= cyl(BLOCK_TOP, BORE_R).translate([0, MAG_Y, FLOOR_Z])
    blk -= cyl(9, BORE_R + 3.0).translate([0, MAG_Y, BLOCK_TOP - 8])           # гнездо за тръбата
    # лявото бутало (5 €): канал по X, изход надясно
    blk -= box(wall_a, 0, MAG_Y - 13, MAG_Y + 13, FLOOR_Z, FLOOR_Z + pa + 0.6)
    blk -= box(wall_a - 7, wall_a + 1, MAG_Y - 4.5, MAG_Y + 4.5, za - 4.5, za + 4.5)
    blk -= box(0, 19, MAG_Y - 13.25, MAG_Y + 13.25, FLOOR_Z, FLOOR_Z + ga)
    blk -= box(14, 19, MAG_Y - 13.25, MAG_Y + 13.25, -1, FLOOR_Z + ga)
    # предното бутало (10 €): канал по Y, изход назад
    blk -= box(-13, 13, MAG_Y + wall_a, MAG_Y, FLOOR_Z, FLOOR_Z + pb + 0.6)
    blk -= box(-4.5, 4.5, MAG_Y + wall_a - 7, MAG_Y + wall_a + 1, zb - 4.5, zb + 4.5)
    blk -= box(-13.25, 13.25, MAG_Y, MAG_Y + 19, FLOOR_Z, FLOOR_Z + gb)
    blk -= box(-13.25, 13.25, MAG_Y + 14, MAG_Y + 19, -1, FLOOR_Z + gb)
    # ниши за чашките (чашката влиза малко под ръба на изхода)
    for cx, cy in (CUP_A, CUP_B):
        blk -= cyl(41, 30.5).translate([cx, cy, -1])
    # прозорче отдясно – виждаш колко монети има в тръбата
    blk -= box(10, 19, MAG_Y - 3, MAG_Y + 3, FLOOR_Z + ga + 4, BLOCK_TOP - 12)

    base = box(-PLATE_X - 2, PLATE_X + 2, -64, MAG_Y + CUP_OFF + 33, 0, 4) + blk
    ring = cyl(3, 31.5) - cyl(5, 29.5).translate([0, 0, -1])
    for cx, cy in (CUP_A, CUP_B):
        base += ring.translate([cx, cy, 4])

    # странични стени: горният ръб е успореден на плочата на бункера
    y0 = -60.0
    prof = CrossSection([[(y0, 0), (0, 0), (0, plate_underside_z(0) - 0.2), (y0, plate_underside_z(y0) - 0.2)]])
    for x0 in (-PLATE_X, CHEEK_X):
        base += prof.extrude(PLATE_X - CHEEK_X).rotate([90, 0, 90]).translate([x0, 0, 0])
        xc = x0 + (PLATE_X - CHEEK_X) / 2
        for y in (-48, -12):
            base += cyl(9, 2.4).translate([xc, y, plate_underside_z(y) - 4.5])
    return base


def make_hopper():
    """Бункер: наклонена плоча + пръстен около диска. Връща в световни координати."""
    plate = box(-PLATE_X, PLATE_X, PLATE_B[0], PLATE_B[1], -PLATE_T, 0)
    ring = cyl(RING_H, RING_ID / 2 + 3) - cyl(RING_H + 2, RING_ID / 2).translate([0, 0, -1])
    hop = plate + ring
    hop -= cyl(40, BOLT_D / 2, center=True)
    hop -= Manifold.cylinder(4.01, 7.65, 7.65, circular_segments=6).translate([0, 0, -PLATE_T - 0.01])  # глава на болта
    hop -= cyl(20, EXIT_D / 2, center=True).translate([0, POCKET_R, 0])
    hop = to_world(hop)
    xc = CHEEK_X + (PLATE_X - CHEEK_X) / 2
    for x in (-xc, xc):
        for y in (-48, -12):
            hop -= cyl(10, 2.7).translate([x, y, plate_underside_z(y) - 5])
    return hop


def make_disc():
    """Диск с гнезда + главина + копче с ръчка (печатна позиция = координати на плочата)."""
    disc = cyl(DISC_T, DISC_R)
    for i in range(POCKETS):
        a = 2 * math.pi * i / POCKETS
        disc -= cyl(10, POCKET_D / 2, center=True).translate([POCKET_R * math.cos(a), POCKET_R * math.sin(a), 0])
    hub = cyl(45, 10)
    knob = cyl(14, 22.5).translate([0, 0, 45])
    for i in range(12):
        a = 2 * math.pi * i / 12
        knob -= cyl(16, 2.5).translate([22.5 * math.cos(a), 22.5 * math.sin(a), 44])
    crank = cyl(22, 5).translate([15, 0, 59])
    part = disc + hub + knob + crank
    part -= cyl(200, BOLT_D / 2, center=True)
    part -= cyl(10, 9.5).translate([0, 0, 59 - 9])
    return part


def make_magazine():
    """Тръба с фуния и задна стена (за да не отскачат монетите)."""
    sock = BLOCK_TOP - 8
    tube_top = FUNNEL_Z - 25
    m = cyl(tube_top - sock, BORE_R + 2.8) + cyl(25, BORE_R + 2.8, 32).translate([0, 0, tube_top - sock])
    m -= cyl(tube_top - sock + 0.01, BORE_R).translate([0, 0, -0.005])
    m -= cyl(25.02, BORE_R, 30).translate([0, 0, tube_top - sock - 0.01])
    hood_h = C_Z + 40 - FUNNEL_Z
    hood = (cyl(hood_h, 32) - cyl(hood_h + 2, 30).translate([0, 0, -1])) ^ box(-40, 40, 2, 40, 0, hood_h)
    m += hood.translate([0, 0, FUNNEL_Z - sock])
    m = m.translate([0, MAG_Y, sock])
    m -= to_world(box(-90, 90, -100, 120, -PLATE_T - 1, 100))  # 1 мм луфт под плочата
    return m


def make_pusher(coins):
    """Бутало + прът. Бутането е в посока +X; прътът е назад (−X)."""
    h = push_h(coins) - 0.4
    body = box(0, PUSHER_LEN, -12.7, 12.7, 0, h)
    rod = box(-ROD_LEN, 0.5, -4, 4, h / 2 - 4, h / 2 + 4)
    return body + rod


def make_handle():
    return box(-10, 10, -15, 15, 0, 12) - box(-4.2, 4.2, -4.2, 4.2, 3, 13)


def make_cup():
    return cyl(34, 29) - cyl(40, 27).translate([0, 0, 2])


# ------------------------------------------------------------------ сглобка
def pusher_a_world(dx=0.0):
    return make_pusher(COINS_A).translate([-RETRACT - PUSHER_LEN + dx, MAG_Y, FLOOR_Z + 0.2])


def pusher_b_world(dy=0.0):
    return make_pusher(COINS_B).rotate([0, 0, 90]).translate([0, MAG_Y - RETRACT - PUSHER_LEN + dy, FLOOR_Z + 0.2])


def handles_world():
    end = -RETRACT - PUSHER_LEN - ROD_LEN + 9           # прътът влиза 9 мм в дръжката
    za = FLOOR_Z + 0.2 + (push_h(COINS_A) - 0.4) / 2
    zb = FLOOR_Z + 0.2 + (push_h(COINS_B) - 0.4) / 2
    ha = make_handle().rotate([0, 90, 0]).translate([end - 12, MAG_Y, za])
    hb = make_handle().rotate([0, 90, 0]).rotate([0, 0, 90]).translate([0, MAG_Y + end - 12, zb])
    return ha, hb


def assembly():
    ha, hb = handles_world()
    cup = make_cup()
    return [("base", make_base()), ("hopper", make_hopper()), ("disc", to_world(make_disc())),
            ("magazine", make_magazine()), ("pusherA", pusher_a_world()), ("pusherB", pusher_b_world()),
            ("handleA", ha), ("handleB", hb),
            ("cupA", cup.translate([*CUP_A, 4])), ("cupB", cup.translate([*CUP_B, 4]))]


# ------------------------------------------------------------------ печатни позиции и плочи за A1
def print_parts():
    """(файл, манифолд в печатна позиция, плоча 1..3, (x, y) център на плочата)."""
    hop = make_hopper().translate([0, 0, -C_Z]).rotate([-TILT, 0, 0])  # плочата надолу
    up = [0, 90, 0]                                                    # буталата прави, прътът нагоре
    return [
        ("1_osnova", make_base(), 1, (95, 132)),
        ("7_chashka_5eur", make_cup(), 1, (214, 52)),
        ("7_chashka_10eur", make_cup(), 1, (214, 118)),
        ("6_drazhka_5eur", make_handle(), 1, (204, 186)),
        ("6_drazhka_10eur", make_handle(), 1, (232, 186)),
        ("2_bunker", hop, 2, (128, 128)),
        ("3_disk", make_disc(), 3, (82, 82)),
        ("4_tryba", make_magazine(), 3, (200, 52)),
        ("5_butalo_5eur", make_pusher(COINS_A).rotate(up), 3, (176, 150)),
        ("5_butalo_10eur", make_pusher(COINS_B).rotate(up), 3, (220, 150)),
    ]


PLATE_NAMES = {1: "Osnova", 2: "Bunker", 3: "Mehanizam"}


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)


def centered(tm):
    """Центрира по XY и слага дъното на Z=0."""
    tm = tm.copy()
    lo, hi = tm.bounds
    tm.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return tm


def mesh_xml(tm, oid, extra=""):
    v = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
    return f'<object id="{oid}" {extra}type="model">\n<mesh>\n<vertices>\n{v}\n</vertices>\n<triangles>\n{t}\n</triangles>\n</mesh>\n</object>'


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="config" ContentType="text/xml"/>
</Types>"""
ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""
NS_CORE = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
NS_BBL = ('xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')


def write_bambu_3mf(path, parts):
    """Един 3MF проект на Bambu Studio с отделна плоча за всяка група части."""
    n = len(parts)
    plates = sorted({p for _, _, p, _ in parts})
    cols = math.ceil(math.sqrt(len(plates)))
    stride = BED * 1.2                       # Bambu Studio подрежда плочите през 1/5 от ширината
    origin = {p: ((i % cols) * stride, -(i // cols) * stride) for i, p in enumerate(plates)}
    uid = lambda: str(uuid.uuid4())

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        comps, items, rels, cfg_objs, assemble = [], [], [], [], []
        cfg_plates = {p: [] for p in plates}
        for i, (name, m, plate, (cx, cy)) in enumerate(parts):
            mid, oid = i + 1, n + i + 1
            tm = centered(to_trimesh(m))
            sub = f"/3D/Objects/object_{mid}.model"
            z.writestr(sub[1:], f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS_CORE} {NS_BBL}>\n'
                                f'<metadata name="BambuStudio:3mfVersion">1</metadata>\n<resources>\n'
                                f'{mesh_xml(tm, mid, 'p:UUID="' + uid() + '" ')}\n</resources>\n<build/>\n</model>')
            rels.append(f'<Relationship Target="{sub}" Id="rel-{mid}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            comps.append(f'<object id="{oid}" p:UUID="{uid()}" type="model">\n<components>\n'
                         f'<component p:path="{sub}" objectid="{mid}" p:UUID="{uid()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                         f'</components>\n</object>')
            ox, oy = origin[plate]
            tr = f"1 0 0 0 1 0 0 0 1 {ox + cx:.3f} {oy + cy:.3f} 0"
            items.append(f'<item objectid="{oid}" p:UUID="{uid()}" transform="{tr}" printable="1"/>')
            support = ('<metadata key="enable_support" value="1"/>\n<metadata key="support_on_build_plate_only" value="1"/>\n'
                       if name == "1_osnova" else "")
            cfg_objs.append(f'<object id="{oid}">\n<metadata key="name" value="{name}"/>\n<metadata key="extruder" value="1"/>\n{support}'
                            f'<part id="{mid}" subtype="normal_part">\n<metadata key="name" value="{name}"/>\n'
                            f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n</part>\n</object>')
            cfg_plates[plate].append(f'<model_instance>\n<metadata key="object_id" value="{oid}"/>\n'
                                     f'<metadata key="instance_id" value="0"/>\n<metadata key="identify_id" value="{100 + i}"/>\n</model_instance>')
            assemble.append(f'<assemble_item object_id="{oid}" instance_id="0" transform="{tr}" offset="0 0 0"/>')

        z.writestr("3D/_rels/3dmodel.model.rels", '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + "\n".join(rels) + "\n</Relationships>")
        z.writestr("3D/3dmodel.model", f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS_CORE} {NS_BBL}>\n'
                   '<metadata name="Application">BambuStudio-01.09.07.52</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                   '<metadata name="Title">Monetomat 50c</metadata>\n<resources>\n' + "\n".join(comps) +
                   f'\n</resources>\n<build p:UUID="{uid()}">\n' + "\n".join(items) + "\n</build>\n</model>")
        plate_xml = []
        for p in plates:
            plate_xml.append(f'<plate>\n<metadata key="plater_id" value="{p}"/>\n<metadata key="plater_name" value="{PLATE_NAMES[p]}"/>\n'
                             '<metadata key="locked" value="false"/>\n' + "\n".join(cfg_plates[p]) + "\n</plate>")
        z.writestr("Metadata/model_settings.config", '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(cfg_objs) + "\n" +
                   "\n".join(plate_xml) + "\n<assemble>\n" + "\n".join(assemble) + "\n</assemble>\n</config>")


def write_plain_3mf(path, parts):
    """Обикновен 3MF (една плоча) – отваря се във всеки слайсер."""
    objs, items = [], []
    for i, (name, m, _, (cx, cy)) in enumerate(parts):
        tm = centered(to_trimesh(m))
        objs.append(mesh_xml(tm, i + 1, f'name="{name}" '))
        items.append(f'<item objectid="{i + 1}" transform="1 0 0 0 1 0 0 0 1 {cx:.3f} {cy:.3f} 0"/>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("3D/3dmodel.model", f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS_CORE}>\n'
                   '<resources>\n' + "\n".join(objs) + "\n</resources>\n<build>\n" + "\n".join(items) + "\n</build>\n</model>")


def export_preview(path):
    """Частите в сглобено положение (база64) за preview.html. Дискът и буталата са в собствени координати."""
    parts = dict(assembly())
    parts["disc"] = make_disc()
    data = {}
    for name, m in parts.items():
        buf = io.BytesIO()
        to_trimesh(m).export(buf, file_type="stl")
        data[name] = base64.b64encode(buf.getvalue()).decode()
    consts = dict(C_Z=C_Z, TILT=TILT, MAG_Y=MAG_Y, FLOOR_Z=FLOOR_Z, COIN_D=COIN_D, COIN_T=COIN_T,
                  POCKETS=POCKETS, POCKET_R=POCKET_R, PLATE_T=PLATE_T, STROKE=STROKE, COINS_A=COINS_A, COINS_B=COINS_B,
                  FUNNEL_Z=FUNNEL_Z, CUP_A=CUP_A, CUP_B=CUP_B, DISC_R=DISC_R)
    with open(path, "w") as f:
        f.write("window.MACHINE=" + json.dumps({"stl": data, "c": consts}) + ";\n")


def main():
    stl_dir = os.path.join(HERE, "stl")
    os.makedirs(stl_dir, exist_ok=True)
    for f in os.listdir(stl_dir):
        os.remove(os.path.join(stl_dir, f))
    parts = print_parts()
    for name, m, plate, (cx, cy) in parts:
        tm = centered(to_trimesh(m))
        assert tm.is_watertight, name
        tm.export(os.path.join(stl_dir, name + ".stl"))
        sx, sy, sz = tm.extents
        fits = abs(cx) + sx / 2 <= BED and abs(cy) + sy / 2 <= BED and sz <= BED
        print(f"плоча {plate}  {name:<18} {sx:6.1f} × {sy:6.1f} × {sz:6.1f} mm  {tm.volume / 1000:6.1f} cm³{'' if fits else '  !!'}")
    write_bambu_3mf(os.path.join(HERE, "monetomat_A1.3mf"), parts)
    for p, title in PLATE_NAMES.items():
        write_plain_3mf(os.path.join(HERE, f"plocha_{p}_{title.lower()}.3mf"), [x for x in parts if x[2] == p])
    export_preview(os.path.join(HERE, "preview_data.js"))


if __name__ == "__main__":
    main()
