"""Обща геометрия, шрифт и SVG рендер за концепциите LabCoin 2027.

Монетата е шестоъгълник с плосък връх (като 2026), радиус 100 единици.
Ос Y сочи надолу (както в SVG).
"""
import math
import colorsys

import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union, transform

R = 100.0
S3 = math.sqrt(3)
AP = R * S3 / 2          # апотема: горен ръб е при y = -86.6
GAP = 2.4                # процеп между отделни парчета


# ---------------------------------------------------------------- основни
def hexagon(r=R, cx=0.0, cy=0.0, rot=0.0):
    """rot=0 -> плосък връх (като монетата), rot=30 -> остър връх."""
    return Polygon([(cx + r * math.cos(math.radians(rot + 60 * k)),
                     cy + r * math.sin(math.radians(rot + 60 * k))) for k in range(6)])


HEX = hexagon()
V = [(R * math.cos(math.radians(60 * k)), R * math.sin(math.radians(60 * k))) for k in range(6)]


def U(*gs):
    flat = []
    for g in gs:
        if g is None:
            continue
        if isinstance(g, (list, tuple)):
            flat.extend(x for x in g if x is not None)
        else:
            flat.append(g)
    return unary_union(flat) if flat else Polygon()


def inset(g, d):
    return g.buffer(-d, join_style='mitre', mitre_limit=10)


def grow(g, d):
    return g.buffer(d, join_style='mitre', mitre_limit=10)


def T(g, dx, dy):
    return affinity.translate(g, dx, dy)


def Rot(g, deg, origin=(0, 0)):
    return affinity.rotate(g, deg, origin=origin)


def Sc(g, sx, sy=None, origin=(0, 0)):
    return affinity.scale(g, sx, sx if sy is None else sy, origin=origin)


def circle(r, cx=0.0, cy=0.0, res=64):
    return Point(cx, cy).buffer(r, quad_segs=res // 4)


def center(g, cx=0.0, cy=0.0):
    b = g.bounds
    return T(g, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)


def fit(g, w, h, cx=0.0, cy=0.0):
    b = g.bounds
    s = min(w / (b[2] - b[0]), h / (b[3] - b[1]))
    return center(Sc(g, s), cx, cy)


def stroke(pts, t, cap='square', join='mitre'):
    return LineString(pts).buffer(t / 2, cap_style=cap, join_style=join, mitre_limit=10)


def ring(pts, t):
    p = Polygon(pts)
    return p.buffer(t / 2, join_style='mitre', mitre_limit=10).difference(
        p.buffer(-t / 2, join_style='mitre', mitre_limit=10))


def chamf(xa, ya, xb, yb, c):
    return [(xa + c, ya), (xb - c, ya), (xb, ya + c), (xb, yb - c),
            (xb - c, yb), (xa + c, yb), (xa, yb - c), (xa, ya + c)]


def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    if hasattr(g, 'geoms'):
        out = []
        for x in g.geoms:
            out += polys(x)
        return out
    return []


def split(region, lines, gap=GAP):
    cuts = U([LineString(l).buffer(gap / 2, cap_style='square', join_style='mitre') for l in lines])
    return polys(region.difference(cuts))


def affine_quad(g, p0, p1, p3, size=100.0):
    """Изобразява локален квадрат [0,size]^2 върху успоредник p0 (горе-ляво), p1 (горе-дясно), p3 (долу-ляво)."""
    a = (p1[0] - p0[0]) / size
    b = (p3[0] - p0[0]) / size
    d = (p1[1] - p0[1]) / size
    e = (p3[1] - p0[1]) / size
    return affinity.affine_transform(g, [a, b, d, e, p0[0], p0[1]])


def sweep(g, v):
    """Сума на Минковски на g с отсечка v – дълга сянка / екструзия."""
    parts = [g, T(g, *v)]
    for p in polys(g):
        for rg in [p.exterior, *p.interiors]:
            cs = list(rg.coords)
            for (x1, y1), (x2, y2) in zip(cs, cs[1:]):
                q = Polygon([(x1, y1), (x2, y2), (x2 + v[0], y2 + v[1]), (x1 + v[0], y1 + v[1])])
                if q.is_valid and q.area > 1e-6:
                    parts.append(q)
    return U(parts)


def hexpt(r, ang):
    """Точка върху контура на шестоъгълник с плосък връх (радиус r) в посока ang (градуси)."""
    a = (ang % 60) - 30
    d = r * math.cos(math.radians(30)) / math.cos(math.radians(a))
    return d * math.cos(math.radians(ang)), d * math.sin(math.radians(ang))


# ---------------------------------------------------------------- шрифт
WID = {'L': .56, 'A': .74, 'B': .64, 'C': .62, 'O': .70, 'N': .70,
       '2': .58, '0': .58, '7': .56,
       'a': .58, 'b': .58, 'c': .54, 'o': .58, 'n': .56, ' ': .30}
NARROW = {'I', 'l', 'i', '·'}


def glyph(ch, w, h, t, c=None, apex='flat', dot='square'):
    """Ъгловат „лабораторен“ шрифт със скосени ъгли. Връща геометрия в кутия (0,0)-(w,h)."""
    c = t * 0.9 if c is None else c
    x0, x1, y0, y1 = t / 2, w - t / 2, t / 2, h - t / 2
    S = lambda pts: stroke(pts, t)
    xh = h * 0.6
    yt = h - xh + t / 2
    cl = min(c, (y1 - yt) / 2.6)          # скосяване за малките букви
    if ch == 'L':
        g = S([(x0, y0), (x0, y1 - c * .6), (x0 + c * .6, y1), (x1, y1)])
    elif ch == 'A' and apex == 'point':
        a = t * 0.45
        outer = Polygon([(0, h), (w / 2 - a, 0), (w / 2 + a, 0), (w, h)])
        th = math.atan2(w / 2 - a, h)
        tw = t / math.cos(th)
        legL = Polygon([(0, h), (w / 2 - a, 0), (w / 2 - a + tw, 0), (tw, h)])
        legR = Polygon([(w, h), (w / 2 + a, 0), (w / 2 + a - tw, 0), (w - tw, h)])
        yb = h * 0.62
        g = U(legL, legR, box(0, yb - t / 2, w, yb + t / 2).intersection(outer)).intersection(outer)
    elif ch == 'A':
        yb = y0 + (y1 - y0) * 0.56
        g = U(S([(x0, y1), (x0, y0 + c), (x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1)]),
              S([(x0, yb), (x1, yb)]))
    elif ch == 'B':
        ym = y0 + (y1 - y0) * 0.47
        xt = x1 - w * 0.07
        cc = min(c, (ym - y0) / 2.2)
        g = U(S([(x0, y0), (x0, y1)]),
              S([(x0, y0), (xt - cc, y0), (xt, y0 + cc), (xt, ym - cc), (xt - cc, ym), (x0, ym)]),
              S([(x0, ym), (x1 - cc, ym), (x1, ym + cc), (x1, y1 - cc), (x1 - cc, y1), (x0, y1)]))
    elif ch == 'C':
        g = S([(x1, y0), (x0 + c, y0), (x0, y0 + c), (x0, y1 - c), (x0 + c, y1), (x1, y1)])
    elif ch in 'O0':
        g = ring(chamf(x0, y0, x1, y1, c), t)
    elif ch == 'I':
        g = S([(w / 2, y0), (w / 2, y1)])
    elif ch == 'N':
        d = t * 1.25
        g = U(S([(x0, y0), (x0, y1)]), S([(x1, y0), (x1, y1)]),
              Polygon([(0, 0), (d, 0), (w, h), (w - d, h)]))
    elif ch == '2':
        ym = (y0 + y1) / 2
        c2 = min(c, (y1 - y0) / 5)
        g = S([(x0, y0), (x1 - c2, y0), (x1, y0 + c2), (x1, ym - c2), (x1 - c2, ym),
               (x0 + c2, ym), (x0, ym + c2), (x0, y1), (x1, y1)])
    elif ch == '7':
        d = t * 1.25
        g = U(S([(x0, y0), (x1, y0)]),
              Polygon([(w - d, 0), (w, 0), (w, t * .2), (w * .28 + d, h), (w * .28, h)]))
    elif ch == 'l':
        g = S([(w / 2, y0), (w / 2, y1)])
    elif ch == 'i':
        if dot == 'hex':
            dg = hexagon(t * .62, w / 2, t * .55, rot=30)
        else:
            dg = box(0, 0, t, t)
        g = U(S([(w / 2, yt), (w / 2, y1)]), dg)
    elif ch == 'a':
        g = U(ring(chamf(x0, yt, x1, y1, cl), t), S([(x1, yt), (x1, y1)]))
    elif ch == 'b':
        g = U(S([(x0, y0), (x0, y1)]), ring(chamf(x0, yt, x1, y1, cl), t))
    elif ch == 'c':
        g = S([(x1, yt), (x0 + cl, yt), (x0, yt + cl), (x0, y1 - cl), (x0 + cl, y1), (x1, y1)])
    elif ch == 'o':
        g = ring(chamf(x0, yt, x1, y1, cl), t)
    elif ch == 'n':
        g = S([(x0, y1), (x0, yt), (x1 - cl, yt), (x1, yt + cl), (x1, y1)])
    elif ch == '·':
        g = box(0, h / 2 - t / 2, t, h / 2 + t / 2)
    else:
        raise ValueError(ch)
    return g.intersection(box(0, 0, w, h))


def text(s, h, t=None, track=None, c=None, apex='flat', dot='square', wmul=None):
    t = h * 0.19 if t is None else t
    track = t * 0.65 if track is None else track
    wmul = wmul or {}
    x = 0.0
    parts, boxes = [], []
    for ch in s:
        if ch == ' ':
            x += h * WID[' ']
            continue
        w = t if ch in NARROW else h * WID[ch] * wmul.get(ch, 1)
        parts.append(T(glyph(ch, w, h, t, c, apex, dot), x, 0))
        boxes.append((ch, x, w))
        x += w + track
    return U(parts), boxes


def txt(s, h, cx=0.0, cy=0.0, rot=0.0, maxw=None, **kw):
    g, _ = text(s, h, **kw)
    b = g.bounds
    if maxw and b[2] - b[0] > maxw:
        g = Sc(g, maxw / (b[2] - b[0]))
    g = center(g, cx, cy)
    if rot:
        g = Rot(g, rot, origin=(cx, cy))
    return g


def letter(ch, w, h, cx, cy, t=None, **kw):
    """Една буква, вписана в кутия w x h с център (cx, cy)."""
    t = h * 0.2 if t is None else t
    gw = t if ch in NARROW else h * WID.get(ch, .6)
    return fit(glyph(ch, gw, h, t, **kw), w, h, cx, cy)


# ---------------------------------------------------------------- цветове
def _rgb(hx):
    hx = hx.lstrip('#')
    return tuple(int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(hx, dl):
    r, g, b = _rgb(hx)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0, min(1, l + dl))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


# ---------------------------------------------------------------- дизайн + рендер
class Design:
    def __init__(self, title, desc, mech, color, accent=None):
        self.title, self.desc, self.mech = title, desc, mech
        self.color = color
        self.accent = accent or shade(color, .3)
        self.layers = []

    def add(self, kind, g, **kw):
        if g is not None and not g.is_empty:
            self.layers.append((kind, g, kw))
        return self


def path_d(g):
    out = []
    for p in polys(g):
        for rg in [p.exterior, *p.interiors]:
            cs = list(rg.coords)[:-1]
            if len(cs) < 3:
                continue
            out.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in cs) + 'Z')
    return ''.join(out)


def _p(g, fill, extra=''):
    d = path_d(g)
    if not d:
        return ''
    return f'<path d="{d}" fill="{fill}" fill-rule="evenodd"{extra}/>'


def render(d, uid):
    c, acc = d.color, d.accent
    sty = {
        'tray':     dict(fill=shade(c, -.13), edge=shade(c, -.27), off=(0, 5)),
        'body':     dict(fill=c, edge=shade(c, -.22), off=(0, 5)),
        'piece':    dict(fill=c, edge=shade(c, -.24), off=(0, 2.2)),
        'raised':   dict(fill=shade(c, .17), edge=shade(c, -.16), off=(.8, 1.4)),
        'accent':   dict(fill=acc, edge=shade(acc, -.22), off=(.8, 1.4)),
        'engraved': dict(fill=shade(c, -.16), edge=shade(c, -.28), off=(1.0, 1.6)),
        'flat':     dict(fill=c, edge=None, off=(0, 0)),
    }
    solid = U([g for k, g, kw in d.layers if k in ('tray', 'body')])
    out = [f'<defs><filter id="sh{uid}" x="-20%" y="-20%" width="140%" height="140%">'
           f'<feGaussianBlur stdDeviation="3.2"/></filter>'
           f'<filter id="gl{uid}" x="-30%" y="-30%" width="160%" height="160%">'
           f'<feGaussianBlur stdDeviation="2.2"/></filter></defs>']
    if not solid.is_empty:
        out.append(_p(T(solid, 2, 8), 'rgba(0,0,0,.28)', f' filter="url(#sh{uid})"'))
    for kind, g, kw in d.layers:
        st = dict(sty[kind])
        if 'on' in kw:                       # гравюра върху друг цвят
            st['fill'], st['edge'] = shade(kw['on'], -.12), shade(kw['on'], -.26)
        if 'fill' in kw:
            st['fill'] = kw['fill']
            st['edge'] = kw.get('edge', shade(kw['fill'], -.2 if kind != 'engraved' else -.14))
        if 'edge' in kw:
            st['edge'] = kw['edge']
        if 'off' in kw:
            st['off'] = kw['off']
        if kw.get('shadow'):
            out.append(_p(T(g, 3, 7), 'rgba(0,0,0,.30)', f' filter="url(#sh{uid})"'))
        if kw.get('glow'):
            out.append(_p(g, st['fill'], f' filter="url(#gl{uid})" opacity=".85"'))
        if kind == 'engraved':
            out.append(_p(g, st['fill']))
            wall = g.difference(T(g, *st['off']))
            out.append(_p(wall, st['edge']))
        else:
            if st['edge'] and st['off'] != (0, 0):
                out.append(_p(T(g, *st['off']), st['edge']))
            out.append(_p(g, st['fill']))
    body = ''.join(x for x in out if x)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-118 -112 236 236" '
            f'width="600" height="600">{body}</svg>')
