#!/usr/bin/env python3
"""LabCoin 2027 – различни разположения на една и съща идея.

Съдържание на всяка монета: LAB, COIN, 2027 и шестоъгълно гнездо за стикер.
Нива: 0 основа, 1 изпъкнало веднъж, 2 изпъкнало два пъти.

    python3 labcoin-2027/layouts.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from shapely.geometry import Point, Polygon, box  # noqa: E402
from geom import (HEX, U, inset, grow, T, Rot, Sc, hexagon, center, stroke, polys,  # noqa: E402
                  path_d, hexpt, AP)

K = 1 / math.sqrt(3)            # tan 30°: 60° наклон
C30 = math.cos(math.radians(30))
SIZE_MM = 60.0
M = 7.0                         # поле от ръба
INNER = inset(HEX, M)

# ================================================================= шрифт
# hx = колко „шестоъгълни“ са ъглите: 0 – прави, 1 – C е половин шестоъгълник, O е цял.
WID = {'L': .50, 'A': .70, 'B': .60, 'C': .56, 'O': .70, 'N': .64, '2': .54, '0': .56, '7': .52}


def glyph(ch, w, h, t, hx=0.5, bar=0.56):
    x0, x1, y0, y1 = t / 2, w - t / 2, t / 2, h - t / 2
    half = (y1 - y0) / 2
    c = hx * half
    S = lambda p: stroke(p, t)
    if ch == 'L':
        g = S([(x0, y0), (x0, y1), (x1, y1)])
    elif ch == '<':                                    # L от скицата: „<“ със стъпало
        dx = half * K
        g = S([(x0 + dx, y0), (x0, y0 + half), (x0 + dx, y1), (x1, y1)])
    elif ch == 'A':
        yb = y0 + (y1 - y0) * bar
        g = U(S([(x0, y1), (x0, y0 + c), (x0 + c * K, y0), (x1 - c * K, y0), (x1, y0 + c), (x1, y1)]),
              S([(x0, yb), (x1, yb)]))
    elif ch == 'B':
        ym = y0 + (y1 - y0) * .48
        ct, cb = hx * (ym - y0) / 2, hx * (y1 - ym) / 2
        xt = x1 - w * .06
        g = U(S([(x0, y0), (x0, y1)]),
              S([(x0, y0), (xt - ct * K, y0), (xt, y0 + ct), (xt, ym - ct), (xt - ct * K, ym), (x0, ym)]),
              S([(x0, ym), (x1 - cb * K, ym), (x1, ym + cb), (x1, y1 - cb), (x1 - cb * K, y1), (x0, y1)]))
    elif ch == 'C':
        g = S([(x1, y0), (x0 + c * K, y0), (x0, y0 + c), (x0, y1 - c), (x0 + c * K, y1), (x1, y1)])
    elif ch in 'O0':
        p = Polygon([(x0 + c * K, y0), (x1 - c * K, y0), (x1, y0 + c), (x1, y1 - c),
                     (x1 - c * K, y1), (x0 + c * K, y1), (x0, y1 - c), (x0, y0 + c)])
        g = p.buffer(t / 2, join_style='mitre').difference(p.buffer(-t / 2, join_style='mitre'))
    elif ch == 'I':
        g = S([(w / 2, y0), (w / 2, y1)])
    elif ch == 'N':
        d = t * 1.2
        g = U(S([(x0, y0), (x0, y1)]), S([(x1, y0), (x1, y1)]), Polygon([(0, 0), (d, 0), (w, h), (w - d, h)]))
    elif ch == '2':
        ym = (y0 + y1) / 2
        c2 = min(c, (ym - y0) / 2)
        g = S([(x0, y0), (x1 - c2 * K, y0), (x1, y0 + c2), (x1, ym - c2), (x1 - c2 * K, ym),
               (x0 + c2 * K, ym), (x0, ym + c2), (x0, y1), (x1, y1)])
    elif ch == '7':
        xb = max(x0, x1 - (y1 - y0) * K)
        g = S([(x0, y0), (x1, y0), (xb, y1)])
    else:
        raise ValueError(ch)
    return g.intersection(box(0, 0, w, h))


def word(s, h, cx=0, cy=0, t=None, track=None, hx=0.5, wmul=None, bar=0.56, parts=False):
    t = h * .2 if t is None else t
    track = t * .7 if track is None else track
    wmul = wmul or {}
    x, out = 0.0, []
    for ch in s:
        if ch == ' ':
            x += h * .35
            continue
        w = t if ch == 'I' else h * WID.get(ch, WID.get('L')) * wmul.get(ch, 1)
        if ch == '<':
            w = h * .56 * wmul.get(ch, 1)
        out.append(T(glyph(ch, w, h, t, hx, bar), x, 0))
        x += w + track
    g = U(out)
    b = g.bounds
    dx, dy = cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2
    if parts:
        return [T(p, dx, dy) for p in out]
    return T(g, dx, dy)


def turn(g, deg, origin):
    return Rot(g, deg, origin=origin)


# ================================================================= помощни форми
def banner(cx, cy, hw, hh):
    d = hh * K
    return Polygon([(cx - hw, cy), (cx - hw + d, cy - hh), (cx + hw - d, cy - hh),
                    (cx + hw, cy), (cx + hw - d, cy + hh), (cx - hw + d, cy + hh)])


def fit_hex(region, gap=2.5, cx=None, rmax=40):
    """Най-големият шестоъгълник (плосък връх), който влиза в region с луфт gap."""
    reg = inset(region, gap)
    b = reg.bounds
    cx = (b[0] + b[2]) / 2 if cx is None else cx
    best = None
    for i in range(80):
        y = b[1] + (b[3] - b[1]) * i / 79
        lo, hi = 0.0, rmax
        if not reg.contains(Point(cx, y)):
            continue
        for _ in range(22):
            mid = (lo + hi) / 2
            if reg.contains(hexagon(mid, cx, y)):
                lo = mid
            else:
                hi = mid
        if best is None or lo > best[0] + 1e-6:
            best = (lo, cx, y)
    r, x, y = best
    return hexagon(r, x, y)


def counter_of(letter_geom):
    """Затворената вътрешност (дупката) на буква – напр. горната част на A."""
    for p in polys(letter_geom):
        if p.interiors:
            return max((Polygon(i) for i in p.interiors), key=lambda q: q.area)
    return None


def pocket_ring(sticker, w=2.6, gap=1.6):
    """Тънка рамка около гнездото за стикер."""
    return grow(sticker, gap + w).difference(grow(sticker, gap))


# ================================================================= разположения
LAYOUTS = []


def layout(title, note):
    def deco(fn):
        LAYOUTS.append((fn, title, note))
        return fn
    return deco


@layout('Класика', 'Три реда: 2027 горе, голямо LAB в средата, COIN долу. Стикерът е в дупката на A.')
def l_classic():
    L, A, B = word('LAB', 58, 0, -4, t=11.5, wmul={'A': 1.22}, bar=.74, hx=.55, parts=True)
    st = fit_hex(counter_of(A))
    return dict(level1=U(banner(0, -64, 44, 10.5), banner(0, 61, 50, 12)),
                level2=U(L, A, B, word('2027', 12.5, 0, -64, hx=.5), word('COIN', 13.5, 0, 61, hx=.6)),
                sticker=st)


@layout('Скицата', 'Разположението от рисунката: L като „<“, A със стикер, B със заострени купи, '
                   'C – половин шестоъгълник, O – шестоъгълник.')
def l_sketch():
    L, A, B = word('<AB', 60, 0, -2, t=11.5, wmul={'A': 1.04}, bar=.7, hx=1.0, parts=True)
    st = fit_hex(counter_of(A))
    trap = None
    return dict(level1=banner(0, -66, 46, 10.5),
                level2=U(L, A, B, word('2027', 12.5, 0, -66, hx=.5), word('COIN', 20, 0, 58, hx=1.0)),
                sticker=st)


@layout('Стикерът е O', 'LAB и COIN едно под друго като блок. O-то на COIN е шестоъгълник, '
                        'а стикерът влиза в него. 2027 е в лента долу.')
def l_sticker_o():
    lab = word('LAB', 44, 0, -38, t=9, hx=.6)
    C, O, I, N = word('COIN', 40, 0, 16, t=8.5, hx=1.0, wmul={'O': 1.45}, parts=True)
    st = fit_hex(counter_of(O), gap=2.2)
    return dict(level1=banner(0, 62, 46, 10),
                level2=U(lab, C, O, I, N, word('2027', 12, 0, 62, hx=.5)),
                sticker=st)


@layout('Пчелна пита', 'Шест клетки като в кошер: 20 | 27 горе, L A B в средата, стикерът в долната. '
                       'Клетките са изпъкнали веднъж, буквите – два пъти.')
def l_cells():
    r, g = 25.0, 4.0
    dx = r * math.sqrt(3) + g
    dy = 1.5 * r + g * C30
    cells = {(-dx / 2, -6 - dy): '20', (dx / 2, -6 - dy): '27',
             (-dx, -6): 'L', (0, -6): 'A', (dx, -6): 'B', (0, -6 + dy): None}
    l1, l2, st = [], [], None
    for (x, y), s in cells.items():
        cell = hexagon(r, x, y, rot=30)
        l1.append(cell)
        if s is None:
            st = hexagon(r * .62, x, y)
        elif len(s) == 2:
            l2.append(word(s, 17, x, y, hx=.5))
        else:
            l2.append(word(s, 28, x, y, hx=.55))
    l2.append(word('COIN', 12.5, 0, 71, hx=.6))
    return dict(level1=U(l1), level2=U(l2), sticker=st)


@layout('Рамка в рамка', 'Вътрешен шестоъгълник, завъртян на 30°. В ъглите остават 2 0 2 7, '
                         'вътре LAB, стикерът и COIN.')
def l_frame():
    ri = 79.0
    fr = hexagon(ri, rot=30).difference(hexagon(ri - 5, rot=30))
    l2 = [word('LAB', 28, 0, -36, hx=.55), word('COIN', 25, 0, 38, hx=.6)]
    st = hexagon(15, 0, 0)
    l2.append(pocket_ring(st))
    for d, ang in zip('2027', (-120, -60, 120, 60)):
        x, y = hexpt(100, ang)
        cx, cy = x * .80, y * .80
        l2.append(word(d, 13, cx, cy, hx=.5))
    for ang in (0, 180):
        x, y = hexpt(100, ang)
        l2.append(hexagon(3.4, x * .83, y * .83))
    return dict(level1=fr, level2=U(l2), sticker=st)


@layout('Голямо A', 'A е покривът на монетата – следва горните ръбове. Под краката му стоят L и B, '
                    'стикерът е в A, 2027 е върху чертата му.')
def l_big_a():
    t = 12.0
    inner = INNER
    band = inner.difference(inset(inner, t))
    roof = band.intersection(box(-99, -99, 99, 4))
    A = roof
    counter = inset(inner, t).intersection(box(-99, -99, 99, -30))
    st = fit_hex(counter, gap=3)
    l1 = box(-99, -30, 99, -14).intersection(inset(inner, t - .5))
    year = word('2027', 9, 0, -22, hx=.5)
    L = word('L', 40, -55, 30, t=10)
    B = word('B', 40, 55, 30, t=10, hx=.8)
    coin = word('COIN', 17, 0, 62, hx=.6)
    return dict(level1=l1, level2=U(A, L, B, coin, year), sticker=st)


@layout('Медал', 'Широк ръб с 2027 горе и COIN долу. В средата голямо LAB, стикерът е в A.')
def l_medal():
    rim = HEX.difference(inset(HEX, 21))
    l2 = []
    for th, s in ((-90, '2027'), (90, 'COIN')):
        x, y = (AP - 10.5) * math.cos(math.radians(th)), (AP - 10.5) * math.sin(math.radians(th))
        l2.append(word(s, 11, x, y, hx=.55))
    for th in (-150, -30, 150, 30):
        x, y = (AP - 10.5) * math.cos(math.radians(th)), (AP - 10.5) * math.sin(math.radians(th))
        l2.append(hexagon(3.2, x, y))
    L, A, B = word('LAB', 50, 0, 0, t=10, wmul={'A': 1.05}, bar=.7, hx=.6, parts=True)
    st = fit_hex(counter_of(A))
    l2 += [L, A, B, inset(HEX, 23.5).boundary.buffer(.9)]
    return dict(level1=rim, level2=U(l2), sticker=st)


@layout('Две нива', 'Горната половина е една повдигната плоча с 2027 и LAB. Стикерът седи на ръба между '
                    'двете половини, COIN е долу върху основата.')
def l_two_tier():
    st = hexagon(14, 0, 14)
    plate = INNER.intersection(box(-99, -99, 99, 14)).difference(grow(st, 4))
    l2 = [word('2027', 12, 0, -64, hx=.5), word('LAB', 42, 0, -30, t=9, hx=.6),
          word('COIN', 24, 0, 53, hx=.6), pocket_ring(st, gap=1.6)]
    return dict(level1=plate, level2=U(l2), sticker=st)


@layout('Вертикално', 'L, A, B едно под друго в средата. COIN и 2027 текат отстрани. '
                      'Стикерът е горе, като глава на колона.')
def l_vertical():
    l2 = []
    for ch, y in (('L', -24), ('A', 15), ('B', 54)):
        l2.append(word(ch, 34, 0, y, t=8.5, hx=.6, wmul={'A': .9, 'L': 1.0}))
    st = hexagon(13, 0, -63)
    l2.append(pocket_ring(st))
    sideL = banner(0, 0, 50, 10)
    left = Rot(sideL, -90, origin=(0, 0))
    left = T(left, -52, 6)
    right = T(Rot(sideL, 90, origin=(0, 0)), 52, 6)
    l2.append(T(Rot(word('COIN', 13, 0, 0, hx=.6), -90, origin=(0, 0)), -52, 6))
    l2.append(T(Rot(word('2027', 13, 0, 0, hx=.5), 90, origin=(0, 0)), 52, 6))
    return dict(level1=U(left, right), level2=U(l2), sticker=st)


@layout('Лента', 'Името на един ред – LAB COIN – върху лента през цялата монета. '
                 'Стикерът е горе, 2027 е голямо долу.')
def l_strip():
    strip = INNER.intersection(box(-99, -13, 99, 13))
    st = hexagon(19, 0, -48)
    l2 = [word('LAB COIN', 15, 0, 0, hx=.6), pocket_ring(st), word('2027', 24, 0, 48, hx=.55)]
    return dict(level1=strip, level2=U(l2), sticker=st)


# ================================================================= рендер
VB = '-104 -92 208 184'


def preview(d, base='#cfd4da'):
    l1, l2 = '#e2e6ea', '#f6f7f8'
    p = lambda g, f, x='': (f'<path d="{path_d(g)}" fill="{f}" fill-rule="evenodd"{x}/>' if not g.is_empty else '')
    sh = lambda g, dx, dy, op: p(T(g, dx, dy), f'rgba(30,40,55,{op})')
    st = d['sticker']
    s = [sh(HEX, 0, 4.5, .55), p(HEX, base),
         p(st, '#9aa3ad'), p(st.difference(T(st, 1, 1.6)), '#7c8691'),
         sh(d['level1'], .9, 1.6, .28), p(d['level1'], l1),
         sh(d['level2'], 1.3, 2.3, .30), p(d['level2'], l2)]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}" width="640" height="566">'
            + ''.join(s) + '</svg>')


def cad(geom, name):
    mm = SIZE_MM / 200.0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{208 * mm:.3f}mm" height="{184 * mm:.3f}mm" '
            f'viewBox="{VB}"><g id="{name}"><path d="{path_d(geom)}" fill="#000" fill-rule="evenodd"/></g></svg>')


def main():
    out = os.path.join(HERE, 'layouts')
    os.makedirs(out, exist_ok=True)
    index = []
    for i, (fn, title, note) in enumerate(LAYOUTS, 1):
        d = fn()
        d['level2'] = d['level2'].difference(grow(d['sticker'], 1.0)).intersection(INNER.buffer(M - 1))
        d['level1'] = d['level1'].difference(grow(d['sticker'], 1.6))
        slug = f'{i:02d}-{fn.__name__[2:].replace("_", "-")}'
        files = {
            f'{slug}.svg': preview(d),
            f'cad/{slug}-0-base.svg': cad(HEX.difference(d['sticker']), 'base'),
            f'cad/{slug}-1-level1.svg': cad(d['level1'], 'level1'),
            f'cad/{slug}-2-level2.svg': cad(d['level2'], 'level2'),
            f'cad/{slug}-sticker.svg': cad(d['sticker'], 'sticker'),
        }
        os.makedirs(os.path.join(out, 'cad'), exist_ok=True)
        for n, s in files.items():
            with open(os.path.join(out, n), 'w', encoding='utf-8') as f:
                f.write(s)
        index.append((slug, title, note))
        print(slug, title)
    with open(os.path.join(out, 'index.txt'), 'w', encoding='utf-8') as f:
        for slug, title, note in index:
            f.write(f'{slug}\t{title}\t{note}\n')


if __name__ == '__main__':
    main()
