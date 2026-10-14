#!/usr/bin/env python3
"""LabCoin 2027 – разчертаване на скицата в един шестоъгълник, 2 нива релеф.

    python3 labcoin-2027/final.py

Ниво 0 – основа (целият шестоъгълник)
Ниво 1 – изпъкнало веднъж: лентата за годината, трапецът под A
Ниво 2 – изпъкнало два пъти: L, A, B, COIN, 2027
Гнездо   – вдлъбнат шестоъгълник за стикер (в A)

Всички наклони са 60° – успоредни на ръбовете на монетата.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from shapely.geometry import Polygon, box  # noqa: E402
from geom import HEX, U, inset, grow, T, hexagon, glyph, center, path_d, polys, shade  # noqa: E402

K = 1 / math.sqrt(3)        # tan 30°: хоризонтално отместване за 60° наклон
SIZE_MM = 60.0              # монетата от връх до връх, в мм (сменя се тук)

# ---------------------------------------------------------------- параметри (единици: R = 100)
M = 6.0       # разстояние от ръба на монетата
TS = 11.0     # дебелина на чертите на L, A, B
G = 6.0       # разстояние между буквите
GAP = 2.5     # луфт около стикера / трапеца


def build(variant):
    inner = inset(HEX, M)
    band = inner.difference(inset(inner, TS))          # лента по ръба, дебелина TS
    tw = TS / math.cos(math.radians(30))               # хоризонтална ширина на 60° черта
    gw = G / math.cos(math.radians(30))

    # ---------------- A
    a0, yT, yB = 16.0, -46.0, 40.0
    xo = lambda y: a0 + (y - yT) * K                    # външен ръб на крака
    A_out = Polygon([(-a0, yT), (a0, yT), (xo(yB), yB), (-xo(yB), yB)])
    ac = a0 + TS * K - tw                               # вътрешна полуширина горе
    yc = yT + TS
    xi = lambda y: ac + (y - yc) * K
    counter = Polygon([(-ac, yc), (ac, yc), (xi(yB + 1), yB + 1), (-xi(yB + 1), yB + 1)])
    rs = 2 * (ac + GAP * K - GAP / math.cos(math.radians(30)))
    yh = yc + GAP + rs * math.sqrt(3) / 2
    sticker = hexagon(rs, 0, yh)
    ybar0 = yh + rs * math.sqrt(3) / 2 + GAP
    ybar1 = ybar0 + TS
    A = A_out.difference(counter.intersection(box(-99, -99, 99, ybar0))) \
             .difference(counter.intersection(box(-99, ybar1, 99, 99)))
    trap = inset(counter.intersection(box(-99, ybar1, 99, yB)), GAP)

    # ---------------- B: гръб „>“ по десните ръбове + наклонено стебло до крака на A
    yTop, yBot = -50.0, 28.0
    xs = lambda y: xo(y) + gw                           # ляв ръб на стеблото
    stem = Polygon([(xs(yTop), yTop), (xs(yTop) + tw, yTop), (xs(yBot) + tw, yBot), (xs(yBot), yBot)])
    right = band.intersection(box(0, yTop, 99, yBot))
    ym = -11.5
    bars = U(box(xs(yTop), yTop, 99, yTop + TS), box(xs(ym), ym - TS / 2, 99, ym + TS / 2))
    B = U(stem, right, bars).intersection(inner).intersection(box(0, yTop, 99, yBot))
    B = B.difference(grow(A_out, G))

    # ---------------- L
    left = band.intersection(box(-99, yTop, 0, yBot))
    if variant == 'sketch':
        L = left                                       # „<“ точно като в скицата
    else:
        foot = box(-99, -TS, -xo(0) - gw, 0)
        L = U(band.intersection(box(-99, yTop, 0, 0)), foot).intersection(inner)
    L = L.difference(grow(A_out, G))

    # ---------------- 2027 в удължен шестоъгълник
    bh, bx = 11.0, 50.0
    banner = Polygon([(-bx, -67), (-bx + bh * K * 1.0, -67 - bh), (bx - bh * K, -67 - bh),
                      (bx, -67), (bx - bh * K, -67 + bh), (-bx + bh * K, -67 + bh)])
    year = row([glyph(c, 8.6, 14, 3.2, c=2.2) for c in '2027'], 3.4)
    year = center(year, 0, -67)

    # ---------------- COIN: C = половин шестоъгълник, O = шестоъгълник
    h, t = 20.0, 4.6
    r = h / math.sqrt(3)
    ring = hexagon(r).difference(hexagon(r - t / math.cos(math.radians(30))))
    C = ring.intersection(box(-99, -99, r * 0.25, 99))
    O = ring
    I = box(-t / 2, -h / 2, t / 2, h / 2)
    nw = 16.0
    N = U(box(0, 0, t, h), box(nw - t, 0, nw, h), Polygon([(0, 0), (t * 1.25, 0), (nw, h), (nw - t * 1.25, h)]))
    N = T(N.intersection(box(0, 0, nw, h)), 0, -h / 2)
    coin = center(row([C, O, I, N], 4.0), 0, 60)

    return dict(
        base=HEX,
        level1=U(banner, trap),
        level2=U(L, A, B, year, coin),
        sticker=sticker,
        info=dict(sticker_across_corners=2 * rs, sticker_center_y=yh),
    )


def row(parts, gap):
    out, x = [], 0.0
    for p in parts:
        b = p.bounds
        out.append(T(p, x - b[0], -(b[1] + b[3]) / 2))
        x += (b[2] - b[0]) + gap
    return U(out)


# ---------------------------------------------------------------- изход
VB = '-104 -92 208 184'


def preview(d, color='#1f9e89'):
    base, l1, l2 = color, shade(color, .10), shade(color, .20)
    e0, e1, e2 = shade(color, -.22), shade(color, -.12), shade(color, -.05)
    p = lambda g, f, extra='': f'<path d="{path_d(g)}" fill="{f}" fill-rule="evenodd"{extra}/>'
    s = [p(T(d['base'], 0, 4), e0), p(d['base'], base),
         p(d['sticker'], shade(color, -.16)), p(d['sticker'].difference(T(d['sticker'], 1, 1.6)), shade(color, -.28)),
         p(T(d['level1'], .8, 1.4), e1), p(d['level1'], l1),
         p(T(d['level2'], 1.2, 2.2), e2), p(T(d['level2'], .6, 1.1), shade(color, .02)), p(d['level2'], l2)]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}" width="640" height="566">{"".join(s)}</svg>'


def levels_map(d):
    p = lambda g, f, st='': f'<path d="{path_d(g)}" fill="{f}" fill-rule="evenodd"{st}/>'
    s = [p(d['base'], '#e9e7e2', ' stroke="#222" stroke-width=".6"'),
         p(d['level1'], '#a8c8e8', ' stroke="#222" stroke-width=".4"'),
         p(d['level2'], '#2c5f9e', ' stroke="#222" stroke-width=".4"'),
         p(d['sticker'], '#fff', ' stroke="#d33" stroke-width=".8" stroke-dasharray="2 1.2"')]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}" width="640" height="566">{"".join(s)}</svg>'


def cad(d, layers):
    """SVG в мм: всички файлове имат еднакъв viewBox, за да съвпадат при внос."""
    mm = SIZE_MM / 200.0
    w, h = 208 * mm, 184 * mm
    g = []
    for name, geom in layers:
        g.append(f'<g id="{name}"><path d="{path_d(geom)}" fill="#000" fill-rule="evenodd"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" viewBox="{VB}">'
            + ''.join(g) + '</svg>')


def main():
    out = os.path.join(HERE, 'final')
    os.makedirs(out, exist_ok=True)
    for v in ('sketch', 'foot'):
        d = build(v)
        files = {
            f'{v}-preview.svg': preview(d),
            f'{v}-levels.svg': levels_map(d),
            f'{v}-0-base.svg': cad(d, [('base', d['base'].difference(d['sticker']))]),
            f'{v}-1-level1.svg': cad(d, [('level1', d['level1'])]),
            f'{v}-2-level2.svg': cad(d, [('level2', d['level2'])]),
            f'{v}-sticker.svg': cad(d, [('sticker', d['sticker'])]),
        }
        for n, s in files.items():
            with open(os.path.join(out, n), 'w', encoding='utf-8') as f:
                f.write(s)
        i = d['info']
        print(v, 'стикер: %.1f мм връх-връх' % (i['sticker_across_corners'] * SIZE_MM / 200))


if __name__ == '__main__':
    main()
