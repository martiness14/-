"""Монетомат: машина с ръчка за монети от 50 евроцента – генератор на STL файлове.

Как работи:
  1. Изсипваш монетите в бункера (наклонен на 45°).
  2. Въртиш дръжката. Дискът има 5 гнезда; всяко гнездо загребва по 1 монета от купа,
     изкачва я горе и я пуска през дупка в задната плоча. Монетата пада в тръба (магазин)
     и монетите се нареждат една върху друга.
  3. Бутваш буталото надясно – отдолу излизат ТОЧНО 10 монети (5 €) и падат в чашката.
     11-тата монета се опира в ръба над изхода и остава в тръбата.
     Две бутвания = 10 €.

Нужни са още: 1 болт M8×80 + 1 шайба M8 + 1 самоконтрираща гайка M8 (оста на диска).

Стартиране:  pip install manifold3d trimesh numpy  &&  python3 generate.py
Всички размери са в милиметри. Световни координати: X надясно, Y навътре (от теб), Z нагоре.
"""
import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

# ---- Монета 50 евроцента ----
COIN_D = 24.25
COIN_T = 2.38

# ---- Дозатор (буталото) ----
COINS_PER_PUSH = 10                    # 10 монети = 5 € на едно бутване
GATE = (COINS_PER_PUSH + 0.5) * COIN_T  # височина на изхода: 10,5 монети – 11-тата се закача за ръба
PUSH_H = (COINS_PER_PUSH - 0.5) * COIN_T  # височина на канала за буталото: не докосва 11-тата монета
BORE_R = 12.75                         # радиус на тръбата (монета + 1,25 мм хлабина)
FLOOR_Z = 45.0                         # височина на дъното на тръбата (под него стои чашката)
MAG_Y = 30.0                           # Y на оста на тръбата
STROKE = 30.0                          # ход на буталото

# ---- Бункер и диск ----
TILT = 45.0                            # наклон на бункера
C_Z = 162.0                            # височина на центъра на диска
PLATE_T = 5.0
DISC_R = 50.0
DISC_T = 2.2                           # малко по-тънък от монетата – в гнездото влиза само 1 монета
POCKETS = 5
POCKET_R = 32.0                        # радиус, на който са гнездата
POCKET_D = COIN_D + 1.15
EXIT_D = 27.0                          # дупката в плочата, през която пада монетата
RING_ID = 2 * DISC_R + 3               # 1,5 мм около диска – по-малко от дебелината на монета
RING_H = 50.0
BOLT_D = 8.6

FUNNEL_Z = C_Z - 15                    # горен ръб на фунията на тръбата

SEG = 96
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")

S = math.sqrt(0.5)


def cyl(h, r, r2=None, center=False):
    return Manifold.cylinder(h, r, r if r2 is None else r2, circular_segments=SEG, center=center)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def to_world(m):
    """От координатите на плочата (център на диска в 0, Z = нормалата на плочата) към света."""
    return m.rotate([TILT, 0, 0]).translate([0, 0, C_Z])


def plate_underside_z(y):
    """Височина на долната страна на плочата на бункера при дадено Y (по оста X=0)."""
    return C_Z + y - PLATE_T / S


# ------------------------------------------------------------------ части
def make_base():
    """Основа: дозатор с канал за буталото + две странични стени, на които лежи бункерът."""
    top = FLOOR_Z + GATE + 15
    blk = box(-55, 18, MAG_Y - 22, MAG_Y + 22, 0, top)
    blk -= cyl(top, BORE_R).translate([0, MAG_Y, FLOOR_Z])
    blk -= cyl(9, BORE_R + 3.0).translate([0, MAG_Y, top - 8])             # гнездо за тръбата
    blk -= box(-49, 0, MAG_Y - 13, MAG_Y + 13, FLOOR_Z, FLOOR_Z + PUSH_H + 0.6)  # канал за буталото
    blk -= box(-56, -48, MAG_Y - 4.5, MAG_Y + 4.5, FLOOR_Z + PUSH_H / 2 - 4.5, FLOOR_Z + PUSH_H / 2 + 4.5)  # отвор за пръта
    blk -= box(0, 19, MAG_Y - 13.25, MAG_Y + 13.25, FLOOR_Z, FLOOR_Z + GATE)  # изход
    blk -= box(14, 19, MAG_Y - 23, MAG_Y + 23, -1, FLOOR_Z + GATE)           # монетите падат оттук в чашката
    blk -= box(-3, 3, MAG_Y - 23, MAG_Y - 10, FLOOR_Z + 4, top - 12)        # прозорче отпред – виждаш монетите

    base = box(-60, 80, -45, 60, 0, 4) + blk
    # пръстен, в който стои чашката
    cup_ring = cyl(4, 31.5) - cyl(5, 29.4).translate([0, 0, -0.5])
    base += cup_ring.translate([45, MAG_Y, 3])

    # странични стени: горният ръб е успореден на плочата на бункера
    for x0 in (-56, 50):
        prof = CrossSection([[(-42, 0), (0, 0), (0, plate_underside_z(0) - 0.2), (-42, plate_underside_z(-42) - 0.2)]])
        wall = prof.extrude(6).rotate([90, 0, 90]).translate([x0, 0, 0])
        base += wall
        for y in (-34, -10):
            base += cyl(9, 2.4).translate([x0 + 3, y, plate_underside_z(y) - 4.5])
    return base


def make_hopper():
    """Бункер: наклонена плоча + пръстен около диска. Връща в световни координати."""
    plate = box(-58, 58, -60, 70, -PLATE_T, 0)
    ring = cyl(RING_H, RING_ID / 2 + 3) - cyl(RING_H + 2, RING_ID / 2).translate([0, 0, -1])
    boss = cyl(4, 13).translate([0, 0, -PLATE_T - 4])
    hop = plate + ring + boss
    hop -= cyl(40, BOLT_D / 2, center=True)
    hop -= Manifold.cylinder(6, 7.6, 7.6, circular_segments=6).translate([0, 0, -PLATE_T - 4.5])  # гнездо за главата на болта
    hop -= cyl(20, EXIT_D / 2, center=True).translate([0, POCKET_R, 0])
    hop = to_world(hop)
    for x in (-53, 53):
        for y in (-34, -10):
            hop -= cyl(10, 2.7).translate([x, y, plate_underside_z(y) - 5])
    return hop


def make_disc():
    """Диск с гнезда + главина + копче с ръчка. Лежи на масата (печатна позиция)."""
    disc = cyl(DISC_T, DISC_R)
    for i in range(POCKETS):
        a = 2 * math.pi * i / POCKETS
        disc -= cyl(10, POCKET_D / 2, center=True).translate([POCKET_R * math.cos(a), POCKET_R * math.sin(a), 0])
    hub = cyl(45, 10)
    knob = cyl(14, 22.5).translate([0, 0, 45])
    for i in range(12):  # грапавини за хващане
        a = 2 * math.pi * i / 12
        knob -= cyl(16, 2.5).translate([22.5 * math.cos(a), 22.5 * math.sin(a), 44])
    crank = cyl(22, 5).translate([14, 0, 59])
    part = disc + hub + knob + crank
    part -= cyl(200, BOLT_D / 2, center=True)
    part -= cyl(10, 9.5).translate([0, 0, 59 - 9])  # място за шайбата и гайката
    return part


def make_magazine():
    """Тръба с фуния и задна стена (за да не отскачат монетите)."""
    sock = FLOOR_Z + GATE + 15 - 8
    tube_top = FUNNEL_Z - 25
    tube = cyl(tube_top - sock, BORE_R + 2.8)
    funnel = cyl(25, BORE_R + 2.8, 32).translate([0, 0, tube_top - sock])
    m = tube + funnel
    m -= cyl(tube_top - sock + 0.01, BORE_R).translate([0, 0, -0.005])
    m -= cyl(25.02, BORE_R, 30).translate([0, 0, tube_top - sock - 0.01])
    m -= box(-3, 3, -40, -5, 8, tube_top - sock - 6)  # прозорче отпред
    # задна стена-качулка
    hood_h = 200 - FUNNEL_Z
    hood = (cyl(hood_h, 32) - cyl(hood_h + 2, 30).translate([0, 0, -1])) ^ box(-40, 40, 2, 40, 0, hood_h)
    m += hood.translate([0, 0, FUNNEL_Z - sock])
    m = m.translate([0, MAG_Y, sock])
    # отрязваме качулката под плочата на бункера (1 мм луфт)
    cut = box(-60, 60, -60, 90, -PLATE_T - 1, 60)
    m -= to_world(cut)
    return m


def make_pusher():
    """Бутало + прът; дръжката е отделна част (лепи се на пръта)."""
    w, h = 25.4, PUSH_H - 0.4
    body = box(0, 34, -w / 2, w / 2, 0, h)
    rod = box(-40, 0.5, -4, 4, h / 2 - 4, h / 2 + 4)
    return body + rod  # печата се легнало: X по масата


def make_handle():
    k = box(-10, 10, -15, 15, 0, 12) - box(-4.2, 4.2, -4.2, 4.2, 4, 13)
    return k


def make_cup():
    return cyl(34, 29) - cyl(40, 27).translate([0, 0, 2])


# ------------------------------------------------------------------ сглобка (за прегледа)
def assembly():
    """Връща (име, манифолд в света) за 3D прегледа."""
    disc = make_disc().translate([0, 0, 0])
    disc_w = to_world(disc)
    pusher_w = make_pusher().translate([-15 - 34, MAG_Y, FLOOR_Z + 0.2])
    handle_w = make_handle().rotate([0, -90, 0]).translate([-89, MAG_Y, FLOOR_Z + PUSH_H / 2])
    cup_w = make_cup().translate([45, MAG_Y, 4])
    return [("base", make_base()), ("hopper", make_hopper()), ("disc", disc_w),
            ("magazine", make_magazine()), ("pusher", pusher_w), ("handle", handle_w), ("cup", cup_w)]


def export_preview(path):
    """Частите в сглобено положение (база64) за preview.html. Дискът е в собствените си координати."""
    import base64
    import json
    import io
    data = {}
    parts = dict(assembly())
    parts["disc"] = make_disc()
    parts["pusher"] = make_pusher()
    for name, m in parts.items():
        buf = io.BytesIO()
        to_trimesh(m).export(buf, file_type="stl")
        data[name] = base64.b64encode(buf.getvalue()).decode()
    consts = dict(C_Z=C_Z, TILT=TILT, MAG_Y=MAG_Y, FLOOR_Z=FLOOR_Z, COIN_D=COIN_D, COIN_T=COIN_T,
                  POCKETS=POCKETS, POCKET_R=POCKET_R, STROKE=STROKE, COINS_PER_PUSH=COINS_PER_PUSH,
                  PUSHER_X=-15 - 34, PUSHER_Z=FLOOR_Z + 0.2, FUNNEL_Z=FUNNEL_Z, CUP_X=45)
    with open(path, "w") as f:
        f.write("window.MACHINE=" + json.dumps({"stl": data, "c": consts}) + ";\n")


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)


def export(m, name):
    tm = to_trimesh(m)
    assert tm.is_watertight, name
    tm.apply_translation([0, 0, -tm.bounds[0][2]])
    tm.export(os.path.join(OUT_DIR, name))
    size = tm.bounds[1] - tm.bounds[0]
    print(f"{name:<22} {size[0]:6.1f} × {size[1]:6.1f} × {size[2]:6.1f} mm  {tm.volume / 1000:6.1f} cm³")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    export(make_base(), "1_osnova.stl")
    # бункерът се печата с плочата надолу
    export(make_hopper().translate([0, 0, -C_Z]).rotate([-TILT, 0, 0]), "2_bunker.stl")
    export(make_disc(), "3_disk.stl")
    export(make_magazine(), "4_tryba.stl")
    export(make_pusher().rotate([90, 0, 0]), "5_butalo.stl")
    export(make_handle(), "6_drazhka.stl")
    export(make_cup(), "7_chashka.stl")
    export_preview(os.path.join(os.path.dirname(OUT_DIR), "preview_data.js"))


if __name__ == "__main__":
    main()
