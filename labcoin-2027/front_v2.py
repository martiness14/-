#!/usr/bin/env python3
"""LabCoin 2027 – лице, версия 2 (черно върху бяло, мм).

Монета: шестоъгълник с плосък връх, 60 мм от връх до връх (като 2026).
Едно правило за всичко: линия 2.4 мм, всички ъгли са скосени на 60° –
успоредно на ръба на монетата. Заради скосяванията редовете влизат един
в друг и процепът между тях става зигзаг (вълната).
Стикер: кръгъл 10 мм, влиза в шестоъгълното 0 (вътрешна апотема 5.1 мм).

    pip install shapely cairosvg
    python3 labcoin-2027/front_v2.py
"""
import math
import os

from shapely import affinity
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'front-v2')

R = 30.0                        # радиус на монетата (до връх), мм
AP = R * math.sqrt(3) / 2       # апотема 25.98
T = 2.4                         # дебелина на линията
G = 0.9                         # процеп
RIM = 2.4                       # ръб
K = 1 / math.sqrt(3)            # tan 30°: хоризонтално отместване при 60° наклон
STICKER = 10.0                  # диаметър на стикера
POCKET_AP = STICKER / 2 + 0.1   # вътрешна апотема на гнездото


def hexagon(ap, cx=0.0, cy=0.0):
    r = ap / math.cos(math.radians(30))
    return Polygon([(cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k)))
                    for k in range(6)])


COIN = hexagon(AP)
RIM_G = COIN.difference(hexagon(AP - RIM))
FIELD = hexagon(AP - RIM - G)


def U(*gs):
    flat = []
    for g in gs:
        if isinstance(g, (list, tuple)):
            flat += [x for x in g if x is not None]
        elif g is not None:
            flat.append(g)
    return unary_union(flat)


def S(pts):
    return LineString(pts).buffer(T / 2, cap_style='square', join_style='mitre', mitre_limit=10)


def mv(g, dx, dy):
    return affinity.translate(g, dx, dy)


def cham_rect(x0, y0, x1, y1, c):
    """Правоъгълник със скосени на 60° ъгли (c = вертикален размер)."""
    d = c * K
    return [(x0 + d, y0), (x1 - d, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - d, y1), (x0 + d, y1), (x0, y1 - c), (x0, y0 + c)]


# ================================================================ шрифт
# Кутия (0,0)-(w,h), Y надолу. Всяка буква се изрязва по един и същи
# скосен силует, затова всички ъгли са еднакви.
def glyph(ch, w, h, c):
    x0, x1, y0, y1 = T / 2, w - T / 2, T / 2, h - T / 2
    ym = (y0 + y1) / 2
    d = c * K
    if ch == 'L':
        g = S([(x0, y0), (x0, y1 - c), (x0 + d, y1), (x1, y1)])
    elif ch == 'A':
        yb = y0 + (y1 - y0) * 0.56
        g = U(S([(x0, y1), (x0, y0 + c), (x0 + d, y0), (x1 - d, y0), (x1, y0 + c), (x1, y1)]),
              S([(x0, yb), (x1, yb)]))
    elif ch == 'B':
        yb = y0 + (y1 - y0) * 0.47
        cb = min(c, (yb - y0) / 2, (y1 - yb) / 2)
        xt = x1 - 0.7
        g = U(S([(x0, y0), (x0, y1)]),
              S([(x0, y1), (x1 - cb * K, y1), (x1, y1 - cb), (x1, yb + cb), (x1 - cb * K, yb), (x0, yb)]),
              S([(x0, y0), (xt - cb * K, y0), (xt, y0 + cb), (xt, yb - cb), (xt - cb * K, yb), (x0, yb)]))
    elif ch == 'C':                                   # половин шестоъгълник
        cc = (y1 - y0) / 2
        g = S([(x1, y0), (x0 + cc * K, y0), (x0, ym), (x0 + cc * K, y1), (x1, y1)])
    elif ch == 'O':
        g = Polygon(cham_rect(x0, y0, x1, y1, c))
        g = g.buffer(T / 2, join_style='mitre').difference(g.buffer(-T / 2, join_style='mitre'))
    elif ch == 'I':
        g = S([(w / 2, y0), (w / 2, y1)])
    elif ch == 'N':
        dd = T * 1.15
        g = U(S([(x0, y0), (x0, y1)]), S([(x1, y0), (x1, y1)]),
              Polygon([(0, 0), (dd, 0), (w, h), (w - dd, h)]))
    elif ch == '2':
        c2 = min(c, (ym - y0) / 2)
        g = S([(x0, y0), (x1 - c2 * K, y0), (x1, y0 + c2), (x1, ym - c2),
               (x1 - c2 * K, ym), (x0 + c2 * K, ym), (x0, ym + c2), (x0, y1), (x1, y1)])
    elif ch == '7':
        xb = max(0.0, w - T * 1.2 - h * K)             # кракът е 60°, ако има място; краищата са равни
        leg = Polygon([(w - T * 1.2, 0), (w, 0), (xb + T * 1.2, h), (xb, h)])
        g = U(box(0, 0, w, T), leg)
    else:
        raise ValueError(ch)
    return g.intersection(box(0, 0, w, h))


WIDTH = {'L': .62, 'A': .80, 'B': .70, 'C': .66, 'O': .78, 'I': 0, 'N': .74, '2': .50, '7': .50}


def char(ch, h, c):
    w = T if ch == 'I' else h * WIDTH[ch]
    return glyph(ch, w, h, c)


def zero(h):
    """0 = малка монета: шестоъгълник с плосък връх, в дупката влиза стикерът."""
    ap = h / 2
    g = hexagon(ap).difference(hexagon(ap - T))
    return mv(g, ap / math.cos(math.radians(30)), ap), mv(hexagon(ap - T), ap / math.cos(math.radians(30)), ap)


def line(items, track, split=None, step=0.0, slide=True, fault=0.0):
    """Подрежда знаците; връща (ред, отместване на всеки знак).
    split: от кой знак нататък блокът се плъзга с step по 60° (разломът)."""
    x, out, offs = 0.0, [], []
    for i, g in enumerate(items):
        b = g.bounds
        dx, dy = x - b[0], 0.0
        if split is not None:
            right = i >= split
            dy = step / 2 if right else -step / 2
            if slide:
                dx += (step / 2 if right else -step / 2) * K  # плъзгане по ръба на монетата
            elif right:
                dx += fault
        out.append(mv(g, dx, dy))
        offs.append((dx, dy))
        x += (b[2] - b[0]) + track
    allg = U(out)
    b = allg.bounds
    cx = -(b[0] + b[2]) / 2
    return mv(allg, cx, 0), [(dx + cx, dy) for dx, dy in offs]


def nest(fixed, moving, gap, direction):
    """Плъзга „moving“ вертикално към „fixed“, докато процепът стане gap."""
    lo, hi = 0.0, 80.0
    for _ in range(60):
        mid = (lo + hi) / 2
        g = mv(moving, 0, direction * mid)
        if g.distance(fixed) >= gap and not g.intersects(fixed):
            lo = mid
        else:
            hi = mid
    return mv(moving, 0, direction * lo)


def compose(H2=15.0, H1=11.0, H3=11.0, c=3.0, track=1.4, row_gap=1.6, step=0.0, slide=True, fault=0.0):
    zg, pocket = zero(H2)
    sp = dict(split=2, step=step, slide=slide, fault=fault) if step else {}
    year, offs = line([char('2', H2, c), zg, char('2', H2, c), char('7', H2, c)], track, **sp)
    year, pocket = mv(year, 0, -H2 / 2), mv(pocket, offs[1][0], offs[1][1] - H2 / 2)
    lab, _ = line([char(ch, H1, c) for ch in 'LAB'], track, **sp)
    coin, _ = line([char(ch, H3, c) for ch in 'COIN'], track, **sp)
    lab = nest(year, mv(lab, 0, -60), row_gap, +1)
    coin = nest(year, mv(coin, 0, 60), row_gap, -1)
    art = U(lab, year, coin)
    b = art.bounds
    dx, dy = -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2
    art = mv(art, dx, dy)
    compose.clipped = art.difference(FIELD).area
    return art.intersection(FIELD), mv(pocket, dx, dy)


VARIANTS = {
    'A-clean': dict(),                                      # три прави реда
    'B-step':  dict(step=4.0, slide=False, fault=0.4, H3=10.0, track=1.2),  # десният блок слиза надолу
    'C-slide': dict(step=4.0),                              # десният блок се плъзга по 60° ръба
}


# ================================================================ изход
def d_of(g):
    out = []
    polys = [g] if g.geom_type == 'Polygon' else list(getattr(g, 'geoms', []))
    for p in polys:
        if p.geom_type != 'Polygon' or p.is_empty:
            continue
        for rg in [p.exterior, *p.interiors]:
            cs = list(rg.coords)[:-1]
            out.append('M' + 'L'.join(f'{x:.3f},{y:.3f}' for x, y in cs) + 'Z')
    return ''.join(out)


def svg(art, pocket, bg=True, sticker=True):
    v = R + 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{2*v}mm" height="{2*v}mm" '
             f'viewBox="{-v} {-v} {2*v} {2*v}">']
    if bg:
        parts.append(f'<rect x="{-v}" y="{-v}" width="{2*v}" height="{2*v}" fill="#fff"/>')
    parts.append(f'<path d="{d_of(U(RIM_G, art))}" fill="#000" fill-rule="evenodd"/>')
    if sticker:
        c = pocket.centroid
        parts.append(f'<circle cx="{c.x:.3f}" cy="{c.y:.3f}" r="{STICKER/2}" fill="none" '
                     f'stroke="#e5332a" stroke-width="0.25" stroke-dasharray="0.8 0.6"/>')
    parts.append('</svg>')
    return ''.join(parts)


def report(name, art):
    over = art.difference(FIELD).area
    b = art.bounds
    print(f'{name:10s} извън полето: {over:5.2f} мм²   x {b[0]:.1f}..{b[2]:.1f}  y {b[1]:.1f}..{b[3]:.1f}')


def main():
    import cairosvg
    os.makedirs(OUT, exist_ok=True)
    for name, kw in VARIANTS.items():
        art, pocket = compose(**kw)
        report(name, art)
        print(f'{"":10s} изрязано от ръба: {compose.clipped:.2f} мм²')
        files = {f'labcoin-2027-front-{name}.svg': svg(art, pocket, sticker=False),
                 f'labcoin-2027-front-{name}-no-background.svg': svg(art, pocket, bg=False, sticker=False)}
        for fn, s in files.items():
            with open(os.path.join(OUT, fn), 'w') as f:
                f.write(s)
        cairosvg.svg2png(bytestring=svg(art, pocket).encode(),
                         write_to=os.path.join(OUT, f'labcoin-2027-front-{name}-preview.png'),
                         output_width=800, output_height=800)


if __name__ == '__main__':
    main()
