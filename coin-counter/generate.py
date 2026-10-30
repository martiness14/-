"""Броач-тава за монети от 50 евроцента – генератор на STL файлове.

Идея: изсипваш шепа монети в рамката, разклащаш я наляво-надясно и монетите
падат на ребро в улеите на касетките. Всяка касетка побира ТОЧНО определен брой
монети (20 бр. = 10 € или 10 бр. = 5 €) – 21-вата монета просто няма място.
Излишните монети се изсипват обратно през ниската предна стена.
После вадиш пълните касетки за ушите – всяка касетка е готова пачка.

Стартиране:  pip install manifold3d trimesh numpy  &&  python3 generate.py
Всички размери са в милиметри.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

# ---- Монета 50 евроцента (официални размери) ----
COIN_D = 24.25        # диаметър
COIN_T = 2.38         # дебелина

# ---- Касетка (една пачка) ----
GROOVE_CLEAR = 0.6    # хлабина около монетата в улея (по радиус)
GROOVE_DEPTH = 12.0   # колко дълбоко потъва монетата (≈ половината монета)
LEN_CLEAR = 1.2       # хлабина по дължина (по-малко от 1 монета, за да не влезе още една)
FLOOR = 1.6           # дъно на касетката
RIM = 1.0             # плосък ръб отгоре на страничните стени
CART_W = 30.0         # външна ширина на касетката
END_WALL = 1.8        # дебелина на челните стени
EAR_H = 9.0           # колко стърчат челните стени ("ушите") над ръба

# ---- Рамка (тава) ----
FIT = 0.4             # хлабина между касетките и рамката
FRAME_WALL = 3.0
FRAME_FLOOR = 2.4
FRAME_RISE = 20.0     # колко се издигат задната и страничните стени над касетките
FINGER_HOLE_D = 18.0  # дупка отдолу – натискаш с пръст и касетката изскача

SEGMENTS = 96
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")

# Варианти: (име, монети в пачка, колони, редове)
VARIANTS = [
    ("10eur", 20, 6, 2),   # 12 касетки × 10 € = 120 € на едно разклащане
    ("5eur", 10, 6, 3),    # 18 касетки × 5 € = 90 € на едно разклащане
]


def cart_height():
    return FLOOR + GROOVE_DEPTH


def cart_length(coins):
    return coins * COIN_T + LEN_CLEAR + 2 * END_WALL


def groove_profile():
    """Сечение на улея: кръгло дъно + разширяваща се фуния към ръбовете."""
    r = COIN_D / 2 + GROOVE_CLEAR
    h = cart_height()
    bottom = CrossSection.circle(r, SEGMENTS).translate([0, FLOOR + r])
    top = CrossSection.square([CART_W - 2 * RIM, 10], center=True).translate([0, h + 5])
    return CrossSection.batch_hull([bottom, top])


def make_cart(coins):
    """Касетка с центъра на дъното в (0,0,0); дължината е по Y, височината по Z."""
    h = cart_height()
    length = cart_length(coins)
    inner = coins * COIN_T + LEN_CLEAR

    body = Manifold.cube([CART_W, length, h]).translate([-CART_W / 2, -length / 2, 0])
    # профилът се екструдира по Z, после се завърта така, че да лежи по Y
    groove = groove_profile().extrude(inner).rotate([90, 0, 0]).translate([0, inner / 2, 0])
    cart = body - groove

    ear = Manifold.cube([CART_W, END_WALL, h + EAR_H])
    for y in (-length / 2, length / 2 - END_WALL):
        cart = cart + ear.translate([-CART_W / 2, y, 0])
    # отрязани горни ъгли на ушите – по-лесно се хващат и не дращят
    cut = Manifold.cube([8, 3 * END_WALL, 8], center=True).rotate([0, 45, 0])
    for x in (-CART_W / 2, CART_W / 2):
        cart = cart - cut.translate([x, 0, h + EAR_H])
    return cart


def frame_dims(coins, cols, rows):
    pocket_x = cols * (CART_W + FIT)
    pocket_y = rows * (cart_length(coins) + FIT)
    return pocket_x, pocket_y


def make_frame(coins, cols, rows):
    """Рамка: долният ляв ъгъл е в (0,0,0). Предната стена (Y=0) е ниска – оттам се изсипват излишните монети."""
    px, py = frame_dims(coins, cols, rows)
    ox, oy = px + 2 * FRAME_WALL, py + 2 * FRAME_WALL
    tall = FRAME_FLOOR + cart_height() + FRAME_RISE
    low = FRAME_FLOOR + cart_height()

    frame = Manifold.cube([ox, oy, tall])
    frame -= Manifold.cube([px, py, tall]).translate([FRAME_WALL, FRAME_WALL, FRAME_FLOOR])
    # ниска предна стена, скосена навън като улей за изсипване
    frame -= Manifold.cube([ox + 2, FRAME_WALL + 2, tall]).translate([-1, -1, low])

    # дупки за пръст под всяка касетка
    cart_pitch_y = cart_length(coins) + FIT
    hole = Manifold.cylinder(FRAME_FLOOR * 3, FINGER_HOLE_D / 2, circular_segments=SEGMENTS)
    for c in range(cols):
        for r in range(rows):
            x = FRAME_WALL + (c + 0.5) * (CART_W + FIT)
            y = FRAME_WALL + (r + 0.5) * cart_pitch_y
            frame -= hole.translate([x, y, -FRAME_FLOOR])
    return frame


def export(manifold, name):
    mesh = manifold.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                         faces=np.asarray(mesh.tri_verts), process=True)
    assert tm.is_watertight, name
    path = os.path.join(OUT_DIR, name)
    tm.export(path)
    size = tm.bounds[1] - tm.bounds[0]
    print(f"{name:<28} {size[0]:6.1f} × {size[1]:6.1f} × {size[2]:5.1f} mm  {tm.volume / 1000:6.1f} cm³")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, coins, cols, rows in VARIANTS:
        export(make_cart(coins), f"kasetka_{name}_{coins}moneti.stl")
        export(make_frame(coins, cols, rows), f"ramka_{name}_{cols}x{rows}.stl")


if __name__ == "__main__":
    main()
