#!/usr/bin/env python3
"""LabCoin 2027 – лице, версия 3: „блок“ (lockup).

Целият текст е вписан в един шестоъгълник, успореден на монетата:
  LAB  – трапец: L и B се накланят като горните ръбове, A е с крака на 60°
  2027 – най-широкият ред, изправени цифри, 0 е шестоъгълникът за стикера
  COIN – огледален трапец: C и N се накланят като долните ръбове
Всички наклонени линии са на 60° и са успоредни; процепите са еднакви.

    python3 labcoin-2027/lockup.py
"""
import math
import os

from shapely import affinity
from shapely.geometry import Polygon, box

from front_v2 import (AP, RIM, T, K, STICKER, POCKET_AP, U, mv, hexagon, glyph, svg,
                      cham_rect, report)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'front-v3')

TS = T / math.sin(math.radians(60))   # хоризонтална ширина на линия под 60° (перпендикулярно = T)


def hw(y, ap):
    """Половин ширина на шестоъгълник с апотема ap на височина y."""
    return ap / math.cos(math.radians(30)) - abs(y) * K


def shear(g, h, s):
    """s=+1: горе надясно (/), s=-1: горе наляво (\\). Хоризонталите остават хоризонтални."""
    return affinity.affine_transform(g, [1, -s * K, 0, 1, s * K * h, 0])


# ---------------------------------------------------------------- букви с външна страна по ръба
# Само външната линия на крайната буква е под 60° (успоредна на ръба на монетата);
# всичко вътре е изправено, затова процепите между буквите остават еднакви.
def band(edge, yt, yb, inward):
    """Наклонена линия с перпендикулярна дебелина T по ръба x = edge(y)."""
    return Polygon([(edge(yt), yt), (edge(yt) + inward * TS, yt),
                    (edge(yb) + inward * TS, yb), (edge(yb), yb)])


def L_out(left, yt, yb, xr):
    stem = band(left, yt, yb, +1)
    bar = Polygon([(left(yb - T), yb - T), (xr, yb - T), (xr, yb), (left(yb), yb)])
    return U(stem, bar)


def B_out(right, yt, yb, xl, notch=1.0):
    ym = yt + (yb - yt) * 0.47
    up = lambda y: right(y) - notch
    stem = box(xl, yt, xl + T, yb)
    top = Polygon([(xl, yt), (up(yt), yt), (up(yt + T), yt + T), (xl, yt + T)])
    mid = Polygon([(xl, ym - T / 2), (right(ym - T / 2), ym - T / 2), (right(ym + T / 2), ym + T / 2),
                   (xl, ym + T / 2)])
    bot = Polygon([(xl, yb - T), (right(yb - T), yb - T), (right(yb), yb), (xl, yb)])
    return U(stem, top, mid, bot, band(up, yt, ym, -1), band(right, ym, yb, -1))


def C_out(left, yt, yb, xr):
    stem = band(left, yt, yb, +1)
    top = Polygon([(left(yt), yt), (xr, yt), (xr, yt + T), (left(yt + T), yt + T)])
    bot = Polygon([(left(yb - T), yb - T), (xr, yb - T), (xr, yb), (left(yb), yb)])
    return U(stem, top, bot)


def N_out(right, yt, yb, xl):
    stem = box(xl, yt, xl + T, yb)
    rs = band(right, yt, yb, -1)
    d = TS * 1.05
    diag = Polygon([(xl, yt), (xl + d, yt), (right(yb), yb), (right(yb) - d, yb)])
    shape = Polygon([(xl, yt), (right(yt), yt), (right(yb), yb), (xl, yb)])
    return U(stem, rs, diag).intersection(shape)


def place(g, x, y):
    b = g.bounds
    return mv(g, x - b[0], y - b[1])


# ---------------------------------------------------------------- блок
def compose(margin=1.6, gap=1.6, track=1.6, H2=15.0, H1=11.5, H3=11.5, a_half=6.0, o_w=8.6,
            shift1=-2.8, shift3=-2.4, notch=0.0):
    ap = AP - RIM - margin
    inner = hexagon(ap)
    L_edge = lambda y: -hw(y, ap)
    R_edge = lambda y: hw(y, ap)

    # --- LAB
    yb1 = -H2 / 2 - gap
    yt1 = yb1 - H1
    # A е малко вляво: B се стеснява нагоре, L има място за чертата си
    A = place(glyph('A', 2 * a_half, H1, 3.0), shift1 - a_half, yt1)
    L = L_out(L_edge, yt1, yb1, shift1 - a_half - track)
    B = B_out(R_edge, yt1, yb1, shift1 + a_half + track, notch)
    lab = U(L, A, B)

    # --- 2027 (до ръба при |y| = H2/4, крайните ъгли се режат по 60°)
    zg = hexagon(H2 / 2).difference(hexagon(H2 / 2 - T))
    pocket = hexagon(H2 / 2 - T)
    zw = zg.bounds[2] - zg.bounds[0]
    full = 2 * hw(H2 / 4, ap)
    wd = (full - zw - 3 * track) / 3
    x, parts = -full / 2, []
    for ch in '2_27':
        if ch == '_':
            parts.append(mv(zg, x + zw / 2, 0))
            pocket = mv(pocket, x + zw / 2, 0)
            x += zw + track
        else:
            parts.append(place(glyph(ch, wd, H2, 3.0), x, -H2 / 2))
            x += wd + track
    year = U(parts)

    # --- COIN: O и I изправени и центрирани
    yt3 = H2 / 2 + gap
    yb3 = yt3 + H3
    mid = o_w + track + T
    # O и I са малко вляво: N се стеснява надолу
    O = place(glyph('O', o_w, H3, 3.0), shift3 - mid / 2, yt3)
    I = box(shift3 + mid / 2 - T, yt3, shift3 + mid / 2, yb3)
    C = C_out(L_edge, yt3, yb3, shift3 - mid / 2 - track)
    N = N_out(R_edge, yt3, yb3, shift3 + mid / 2 + track)
    coin = U(C, O, I, N)

    art = U(lab, year, coin)
    compose.clipped = art.difference(inner).area
    return art.intersection(inner), pocket


VARIANTS = {
    'lockup': dict(),
}


def main():
    import cairosvg
    os.makedirs(OUT, exist_ok=True)
    for name, kw in VARIANTS.items():
        art, pocket = compose(**kw)
        report(name, art)
        print(f'{"":10s} изрязано от ръба: {compose.clipped:.2f} мм²')
        for fn, s in {f'labcoin-2027-front-{name}.svg': svg(art, pocket, sticker=False),
                      f'labcoin-2027-front-{name}-no-background.svg': svg(art, pocket, bg=False, sticker=False)}.items():
            with open(os.path.join(OUT, fn), 'w') as f:
                f.write(s)
        cairosvg.svg2png(bytestring=svg(art, pocket).encode(),
                         write_to=os.path.join(OUT, f'labcoin-2027-front-{name}-preview.png'),
                         output_width=800, output_height=800)


if __name__ == '__main__':
    main()
