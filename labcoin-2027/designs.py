"""LabCoin 2027 – 37 концепции. Всяка функция връща Design."""
import math

import numpy as np
from shapely.geometry import Point, Polygon, LineString, box

from geom import (R, S3, AP, GAP, HEX, V, U, inset, grow, T, Rot, Sc, circle, center, fit,
                  stroke, ring, chamf, polys, split, affine_quad, sweep, hexpt, hexagon,
                  glyph, text, txt, letter, Design, shade, WID)

DESIGNS = []


def design(fn):
    DESIGNS.append(fn)
    return fn


def rim(w=4.0):
    return HEX.difference(inset(HEX, w))


def word(s, w, h, cx=0, cy=0, **kw):
    g, _ = text(s, 100, **kw)
    return fit(g, w, h, cx, cy)


# =========================================================== A. LAB запълва монетата
def _hexband_letters():
    m, t, g = 6, 15, 7
    inner = inset(HEX, m)
    band = inner.difference(inset(inner, t))
    top = -(AP - m)
    xg, xa = 34, 27
    L = band.intersection(box(-120, top + t + g, -xg, 120))
    B = U(band.intersection(box(xg, -120, 120, 120)),
          box(xg, top, xg + t, -top), box(xg, -t / 2, 120, t / 2)).intersection(inner)
    ybar = 2
    A = U(band.intersection(box(-xa, -120, xa, top + t)),
          box(-xa, top, -xa + t, -top), box(xa - t, top, xa, -top),
          box(-xa, ybar, xa, ybar + t)).intersection(inner)
    A = A.difference(U(Polygon([(-xa - 1, top - 1), (-xa + 11, top - 1), (-xa - 1, top + 11)]),
                       Polygon([(xa + 1, top - 1), (xa - 11, top - 1), (xa + 1, top + 11)])))
    slot = box(-xa + t, ybar + t, xa - t, 120).intersection(HEX)
    return dict(L=L, A=A, B=B, inner=inner, top=top, t=t, xa=xa, ybar=ybar, slot=slot)


@design
def d_hexband():
    d = Design('LAB по ръба',
               'L, A и B са „изрязани“ от самия шестоъгълник: L се огъва по левите ръбове, B – по десните, '
               'A стои в средата. Под чертата на A има процеп до долния ръб, в който влиза отделна плочка COIN.',
               'Изваждаща се плочка', '#1f9e89', accent='#f3efe4')
    k = _hexband_letters()
    tile = inset(k['slot'], GAP / 2)
    d.add('body', HEX.difference(k['slot']))
    d.add('raised', U(k['L'], k['A'], k['B']))
    d.add('raised', U(txt('20', 11, 0, -40), txt('27', 11, 0, -24)))
    d.add('accent', tile, off=(0, 3))
    d.add('engraved', txt('COIN', 10, 0, 52, rot=-90), on=d.accent)
    return d


@design
def d_openwork():
    d = Design('Ажурна LAB',
               'Същите букви по ръба, но всичко между тях е изрязано – монетата е само рамка от L, A и B. '
               'Долу в средата е отворена, а COIN и 2027 са гравирани върху чертите на A.',
               'Ажур / ключодържател', '#d4a92a')
    k = _hexband_letters()
    letters = U(k['L'], k['A'], k['B'])
    holes = k['inner'].difference(letters)
    d.add('body', HEX.difference(holes).difference(k['slot']))
    d.add('raised', letters.difference(k['slot']))
    t, xa, ybar, top = k['t'], k['xa'], k['ybar'], k['top']
    d.add('engraved', txt('COIN', 8, 0, ybar + t / 2, maxw=44), on=shade(d.color, .09))
    d.add('engraved', txt('2027', 8, 0, top + t / 2, maxw=34), on=shade(d.color, .09))
    return d


@design
def d_stencil():
    d = Design('Шаблон',
               'LAB е прорязано през монетата като шаблон (стенсил) – с мостчета, за да не падат вътрешностите. '
               'С нея може буквално да се рисува LAB с флумастер.',
               'Шаблон за рисуване', '#3a3d44')
    g = word('LAB', 150, 74, 0, -2, t=19)
    bridges = []
    for p in polys(g):
        for it in p.interiors:
            c = Polygon(it).centroid
            bridges.append(box(c.x - 1.8, -200, c.x + 1.8, c.y))
    holes = g.difference(U(bridges))
    d.add('body', HEX.difference(holes))
    d.add('engraved', inset(HEX, 6).boundary.buffer(.7))
    d.add('raised', txt('2027', 10, 0, -60))
    d.add('raised', txt('COIN', 13, 0, 58))
    return d


@design
def d_lower_hex():
    d = Design('lab с шестоъгълни купи',
               'Малки букви, при които „купите“ на a и b са шестоъгълници – същата форма като монетата. '
               'По-мек, приятелски вид.',
               'Релеф', '#e8772e')
    t, rb = 13, 27
    hw = rb * S3 / 2
    yb = 40

    def hring(cx, cy):
        o = hexagon(rb, cx, cy, rot=30)
        return o.difference(inset(o, t))
    l = box(0, -44, t, yb)
    ax = t + 9 + hw
    a = U(hring(ax, yb - rb), box(ax + hw - t, yb - rb - rb / 2, ax + hw, yb))
    bx = ax + hw + 9
    b = U(box(bx, -44, bx + t, yb), hring(bx + hw, yb - rb))
    lab = fit(U(l, a, b), 146, 88, 0, -8)
    d.add('body', HEX)
    d.add('raised', lab)
    d.add('raised', txt('coin', 26, 0, 62, dot='hex', t=5))
    d.add('engraved', txt('2027', 9, 0, -72))
    return d


@design
def d_italic_bleed():
    d = Design('LAB извън ръба',
               'Огромни наклонени букви, които „излизат“ от монетата – ръбът ги реже. '
               'Двуцветен печат: буквите са бели, тялото червено.',
               'Двуцветен печат', '#d23c3c', accent='#f4f1ea')
    g, _ = text('LAB', 100, t=22, track=9)
    g = Rot(g, 0)
    from shapely import affinity
    g = affinity.skew(g, xs=-13, origin=(0, 0))
    g = fit(g, 206, 108, 2, -8).intersection(inset(HEX, 1.5))
    lines = U([box(-120, y - .8, 120, y + .8) for y in (-70, -64, -58)]).intersection(box(-60, -90, 20, 0))
    lines = lines.difference(grow(g, 3)).intersection(inset(HEX, 6))
    d.add('body', HEX)
    d.add('engraved', lines)
    d.add('accent', g)
    tx = affinity.skew(txt('COIN  2027', 10, 0, 0), xs=-13, origin=(0, 0))
    d.add('engraved', center(tx, 0, 70))
    return d


@design
def d_ligature():
    d = Design('Лигатура LAB',
               'Трите букви споделят черти: стъпалото на L влиза в крака на A, а десният крак на A е гръбнакът на B. '
               'Една фигура вместо три букви – лого.',
               'Релеф / лого', '#7b4bc9')
    L = U(box(-82, -55, -62, 55), box(-82, 35, -32, 55))
    A = U(Polygon([(-52, 55), (-29, 55), (1, -55), (-22, -55)]), box(20, -55, 40, 55),
          box(-10, -55, 40, -35), box(-36, -15, 20, 5))
    B = U(stroke([(30, -45), (62, -45), (70, -37), (70, -13), (62, -5), (30, -5)], 20),
          stroke([(30, -5), (67, -5), (75, 3), (75, 37), (67, 45), (30, 45)], 20))
    g = fit(U(L, A, B), 150, 98, 0, -4)
    d.add('body', HEX)
    d.add('raised', rim(4))
    d.add('raised', g)
    d.add('raised', txt('2027', 9, 0, -68))
    d.add('raised', txt('C O I N', 11, 0, 66))
    return d


@design
def d_neon():
    d = Design('Неон',
               'Буквите са само контури – като неонови тръби върху тъмна основа. '
               'Отпечатва се с прозрачна/светеща нишка за контурите.',
               'Светеща нишка', '#1d2340', accent='#ff4fa3')
    g = word('LAB', 150, 70, 0, -10, t=20)
    tubes = g.boundary.buffer(1.7)
    coin = txt('COIN', 20, 0, 52, t=3.2)
    year = txt('2027', 11, 0, -64, t=2.4)
    border = inset(HEX, 8).boundary.buffer(1.4)
    d.add('body', HEX)
    d.add('accent', border, fill='#7af0ff', glow=True, off=(0, 0))
    d.add('accent', tubes, glow=True, off=(0, 0))
    d.add('accent', U(coin, year), fill='#7af0ff', glow=True, off=(0, 0))
    return d


# =========================================================== B. Пъзели от парчета
@design
def d_iso_cube():
    d = Design('Изометричен куб',
               'Шестоъгълникът е разделен на три ромба – окото го вижда като куб. Всяка стена е отделно парче с една буква. '
               'Сглобява се като пъзел от 3 части.',
               'Пъзел, 3 части', '#2f5fd0', accent='#f6f3ea')
    C = (0.0, 0.0)
    faces = [
        ((V[4], V[5], V[3]), [V[4], V[5], C, V[3]], 'L', 'COIN', .12),
        ((V[3], C, V[2]), [V[3], C, V[1], V[2]], 'A', '2027', 0.0),
        ((C, V[5], V[1]), [C, V[5], V[0], V[1]], 'B', '', -.12),
    ]
    d.add('tray', HEX)
    for (p0, p1, p3), quad, ch, small, dl in faces:
        reg = Polygon(quad)
        d.add('piece', inset(reg, GAP / 2), fill=shade(d.color, dl))
        loc = letter(ch, 62, 58, 50, 42)
        if small:
            loc = U(loc, word(small, 56, 10, 50, 82))
        d.add('accent', affine_quad(loc, p0, p1, p3).intersection(inset(reg, 4)))
    return d


@design
def d_seven():
    d = Design('Седем букви',
               '6 триъгълника + център = точно 7 парчета за L-A-B-C-O-I-N. Горе се чете LAB, долу C-O-I-N, '
               'а O е централният шестоъгълник с годината.',
               'Пъзел, 7 части', '#e9e6df', accent='#2b2b2e')
    cen = hexagon(30)
    d.add('tray', HEX, fill='#bdb6a8')
    lets = {3: 'L', 4: 'A', 5: 'B', 2: 'C', 1: 'I', 0: 'N'}
    for k in range(6):
        reg = Polygon([(0, 0), V[k], V[(k + 1) % 6]]).difference(cen)
        d.add('piece', inset(reg, GAP / 2))
        c = reg.centroid
        ang = math.atan2(c.y, c.x)
        cx, cy = c.x + 4 * math.cos(ang), c.y + 4 * math.sin(ang)
        d.add('accent', letter(lets[k], 30, 30, cx, cy).intersection(inset(reg, 4)))
    d.add('piece', inset(cen, GAP / 2), fill='#d6cdbb')
    d.add('accent', hexagon(24).difference(hexagon(17.5)))
    d.add('accent', U(txt('20', 8.5, 0, -5.5), txt('27', 8.5, 0, 6)))
    return d


@design
def d_jigsaw():
    d = Design('Пъзел с шестоъгълни ключалки',
               'Три вертикални парчета (L | A | B), заключени едно в друго с шестоъгълни „уши“ като на пъзел. '
               'Парчетата се вадят и разменят.',
               'Пъзел, 3 части', '#7cbc3a', accent='#20331a')

    def knob(xb, y, s):
        return U(hexagon(8.5, xb + s * 12, y), box(min(xb, xb + s * 5), y - 4.5, max(xb, xb + s * 5), y + 4.5))
    k1, k2, k3, k4 = knob(-34, -52, 1), knob(-34, 52, -1), knob(34, -52, -1), knob(34, 52, 1)
    rL = HEX.intersection(box(-120, -120, -34, 120)).union(k1).difference(k2)
    rM = HEX.intersection(box(-34, -120, 34, 120)).difference(k1).union(k2).difference(k3).union(k4)
    rR = HEX.intersection(box(34, -120, 120, 120)).union(k3).difference(k4)
    d.add('tray', HEX)
    for r, dl in ((rL, .04), (rM, 0), (rR, -.04)):
        d.add('piece', inset(r, GAP / 2), fill=shade(d.color, dl))
    d.add('raised', letter('L', 36, 66, -57, 0))
    d.add('raised', letter('A', 54, 70, 0, 0))
    d.add('raised', letter('B', 36, 66, 57, 0))
    d.add('engraved', txt('2027', 10, 0, -71))
    d.add('engraved', txt('COIN', 10, 0, 71))
    return d


@design
def d_spinner():
    d = Design('Спинър',
               'Три извити „перки“ с L, A и B около въртящ се център с COIN 2027. '
               'Центърът е на лагер (или топче), монетата се върти като фиджет спинър.',
               'Въртящ се център', '#2f5fd0', accent='#ffd23f')
    cen = hexagon(32)
    cuts = []
    for b in (-30, 90, 210):
        cuts.append([(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                     for r, a in ((26, b), (62, b + 18), (130, b + 42))])
    blades = split(HEX.difference(hexagon(32 + GAP)), cuts)
    d.add('tray', HEX)
    for p in blades:
        d.add('piece', inset(p, GAP / 2))
    for ch, th in (('A', -90), ('B', 30), ('L', 150)):
        a = math.radians(th + 14)
        g = letter(ch, 40, 42, 63 * math.cos(a), 63 * math.sin(a))
        d.add('raised', Rot(g, th + 90, origin=(63 * math.cos(a), 63 * math.sin(a))), fill='#f6f3ea')
    d.add('accent', inset(cen, GAP / 2), off=(0, 2.2))
    d.add('engraved', U(txt('COIN', 10, 0, -6), txt('2027', 7.5, 0, 9)), on=d.accent)
    return d


@design
def d_slider():
    d = Design('Плъзгащ пъзел',
               '18 шестоъгълни плочки и едно празно място – като „15“, но в пчелна пита. '
               'Плочките се плъзгат, докато се подредят 2027 / LAB / COIN.',
               'Плъзгащ пъзел', '#3a3d44', accent='#f1ead8')
    s = 18.0
    rows = {-2: ['*', None, '*'], -1: ['2', '0', '2', '7'], 0: ['*', 'L', 'A', 'B', '*'],
            1: ['C', 'O', 'I', 'N'], 2: ['*', '*', '*']}
    d.add('body', HEX)
    recess, tiles, labels, deco = [], [], [], []
    for r, labs in rows.items():
        qs = range(max(-2, -2 - r), min(2, 2 - r) + 1)
        for q, lab in zip(qs, labs):
            x, y = s * S3 * (q + r / 2), 1.5 * s * r
            recess.append(hexagon(s + .9, x, y, rot=30))
            if lab is None:
                continue
            tiles.append(hexagon(s - 1.3, x, y, rot=30))
            if lab == '*':
                deco.append(hexagon(6, x, y).difference(hexagon(3.6, x, y)))
            else:
                labels.append(letter(lab, 15, 16, x, y))
    d.add('engraved', U(recess))
    d.add('accent', U(tiles), off=(.6, 1.8))
    d.add('engraved', U(labels, deco), on=d.accent)
    return d


@design
def d_bands():
    d = Design('Плъзгащи ленти',
               'Три хоризонтални ленти – 2027 / LAB / COIN. Средната се плъзга наляво-надясно като ключалка с шифър; '
               'монетата е „подредена“, когато ръбовете съвпаднат.',
               'Плъзгане / шифър', '#e9e6df', accent='#d23c3c')
    regs = [HEX.intersection(box(-120, -120, 120, -30)), HEX.intersection(box(-120, -30, 120, 30)),
            HEX.intersection(box(-120, 30, 120, 120))]
    dx = 12
    d.add('tray', HEX, fill='#a59d8d')
    d.add('piece', inset(regs[0], GAP / 2))
    d.add('piece', inset(regs[2], GAP / 2))
    d.add('piece', T(inset(regs[1], GAP / 2), dx, 0), fill='#f6f2e8')
    d.add('accent', txt('2027', 24, 0, -57, maxw=92))
    d.add('accent', txt('COIN', 24, 0, 57, maxw=100))
    d.add('accent', txt('LAB', 40, dx, 0))
    arr = U(Polygon([(-78, 0), (-70, -6), (-70, 6)]), Polygon([(78, 0), (70, -6), (70, 6)]))
    d.add('engraved', T(arr, dx, 0), on='#f6f2e8')
    return d


@design
def d_dial():
    d = Design('Шифър-диск',
               'Средният пръстен с L-A-B-C-O-I-N се върти в рамката. Стрелката горе показва коя буква е „избрана“, '
               'а в центъра е годината.',
               'Въртящ се пръстен', '#22325c', accent='#ffd23f')
    frame = HEX.difference(circle(72, res=160))
    rg = circle(69.6, res=160).difference(circle(42.4, res=160))
    core = circle(40, res=160)
    d.add('tray', HEX)
    d.add('piece', frame)
    d.add('piece', rg, fill=shade(d.color, .12))
    d.add('piece', core)
    for i, ch in enumerate('LABCOIN'):
        a = -90 + i * 360 / 7
        x, y = 56 * math.cos(math.radians(a)), 56 * math.sin(math.radians(a))
        d.add('accent', Rot(letter(ch, 18, 20, x, y), a + 90, origin=(x, y)))
        a2 = math.radians(a + 180 / 7)
        d.add('engraved', circle(1.6, 56 * math.cos(a2), 56 * math.sin(a2), 16), on=shade(d.color, .12))
    d.add('accent', Polygon([(-7, -85), (7, -85), (0, -74.5)]))
    for k in range(6):
        x, y = hexpt(88, 60 * k)
        d.add('raised', hexagon(3.4, x * .97, y * .97))
    d.add('raised', U(txt('20', 15, 0, -10), txt('27', 15, 0, 10)))
    return d


@design
def d_glitch():
    d = Design('Разместени диагонали',
               'Монетата е нарязана на три ивици под 60° (по ъгъла на шестоъгълника). Ивиците са разместени – '
               'целта е да ги плъзнеш обратно, докато LAB се подреди.',
               'Плъзгащ пъзел', '#141414', accent='#33e6c4')
    u = (0.5, S3 / 2)
    cuts = [[(x - 150 * u[0], -150 * u[1]), (x + 150 * u[0], 150 * u[1])] for x in (-30, 30)]
    regs = sorted(split(HEX, cuts), key=lambda p: p.centroid.x)
    content = U(word('LAB', 168, 80, 0, -6, t=21), txt('2027', 10, 0, -70), txt('COIN', 12, 0, 68))
    d.add('tray', HEX, fill='#2a2a2a')
    for reg, k in zip(regs, (-7, 7, -2)):
        off = (k * u[0], k * u[1])
        d.add('piece', T(inset(reg, GAP / 2), *off))
        d.add('accent', T(content.intersection(inset(reg, GAP / 2)), *off))
    return d


@design
def d_inlay():
    d = Design('Вадещи се букви',
               'L, A и B са отделни плочки, които „щракват“ в гнезда в монетата (като детски пъзел с форми). '
               'На картинката B е извадена.',
               'Вадещи се плочки', '#e9e6df', accent='#e8772e')
    g = word('LAB', 150, 76, 0, -4, t=19)
    parts = sorted(polys(g), key=lambda p: p.bounds[0])
    d.add('body', HEX)
    d.add('engraved', U([grow(p, 1.8) for p in parts]), fill='#6f6656')
    d.add('accent', U(parts[:2]))
    d.add('engraved', txt('2027', 10, 0, -66))
    d.add('engraved', txt('COIN', 12, 0, 62))
    Bp = Rot(parts[2], 16, origin=parts[2].centroid)
    d.add('accent', T(Bp, 16, -30), shadow=True, off=(1.4, 2.6))
    return d


@design
def d_halves():
    d = Design('Две половини',
               'Монетата се разделя на две половини, захванати със зъби. Горе LAB, долу COIN и годината. '
               'Половинките могат да се раздадат на двама души.',
               'Пъзел, 2 части', '#b8693a', accent='#f3e2c7')
    y0 = 22
    pts = [(-120, y0)]
    for cx, s in ((-50, -1), (0, 1), (50, -1)):
        pts += [(cx - 14, y0), (cx - 8, y0 + s * 11), (cx + 8, y0 + s * 11), (cx + 14, y0)]
    pts += [(120, y0)]
    up = Polygon(pts + [(120, -120), (-120, -120)]).intersection(HEX)
    lo = Polygon(pts + [(120, 120), (-120, 120)]).intersection(HEX)
    d.add('tray', HEX, fill=shade(d.color, -.25))
    d.add('piece', inset(up, GAP / 2))
    d.add('piece', T(inset(lo, GAP / 2), 0, 7))
    d.add('accent', word('LAB', 132, 58, 0, -28, t=20))
    d.add('accent', T(U(txt('COIN', 22, 0, 52), txt('2027', 9, 0, 74)), 0, 7))
    return d


# =========================================================== C. Текстури и техники
@design
def d_honeycomb():
    d = Design('Пчелна пита',
               'LAB е „нарисувано“ с малки шестоъгълни пиксели. Всяка клетка е мини-копие на монетата.',
               'Релеф / текстура', '#f2a541', accent='#3b2a12')
    letters = word('LAB', 162, 82, 0, -14, t=24)
    s = 4.3
    region = inset(HEX, 6).intersection(box(-120, -120, 120, 44))
    on, off = [], []
    for r in range(-30, 31):
        for q in range(-40, 41):
            x, y = s * S3 * (q + r / 2), 1.5 * s * r
            p = Point(x, y)
            if not region.contains(hexagon(s, x, y, rot=30)):
                continue
            (on if letters.contains(p) else off).append((x, y))
    d.add('body', HEX)
    d.add('engraved', U([hexagon(s * .5, x, y, rot=30) for x, y in off]))
    d.add('raised', U([hexagon(s * .92, x, y, rot=30) for x, y in on]), fill='#fff3dc')
    d.add('engraved', box(-70, 47.5, 70, 48.7))
    d.add('raised', txt('COIN 2027', 11, 0, 64, maxw=120))
    return d


SEG7 = {'L': 'def', 'A': 'abcefg', 'b': 'cdefg', 'C': 'adef', 'o': 'cdeg', 'I': 'ef', 'n': 'ceg',
        '2': 'abdeg', '0': 'abcdef', '7': 'abc'}


def seg7(s, W, H, tt, sp, cy, skew=8):
    ends = {'a': ((0, 0), (W, 0)), 'b': ((W, 0), (W, H / 2)), 'c': ((W, H / 2), (W, H)),
            'd': ((0, H), (W, H)), 'e': ((0, H / 2), (0, H)), 'f': ((0, 0), (0, H / 2)),
            'g': ((0, H / 2), (W, H / 2))}
    h, gp = tt / 2, tt * .28
    lit, unlit = [], []
    total = len(s) * W + (len(s) - 1) * sp
    for i, ch in enumerate(s):
        ox = -total / 2 + i * (W + sp)
        for sg, (p, q) in ends.items():
            p, q = np.array(p, float), np.array(q, float)
            u = (q - p) / np.linalg.norm(q - p)
            n = np.array([-u[1], u[0]])
            a, b = p + u * gp, q - u * gp
            pts = [a, a + u * h + n * h, b - u * h + n * h, b, b - u * h - n * h, a + u * h - n * h]
            poly = Polygon([(x + ox, y) for x, y in pts])
            (lit if sg in SEG7[ch] else unlit).append(poly)
    from shapely import affinity
    k = math.tan(math.radians(skew))
    f = lambda g: T(affinity.skew(U(g), xs=-skew, origin=(0, H / 2)), 0, cy - H / 2)
    return f(lit), f(unlit)


@design
def d_seg7():
    d = Design('Дисплей',
               'Като дигитален часовник: буквите са от седемсегментни шестоъгълни сегменти. '
               'Незапалените сегменти са леко вдлъбнати, светещите – от прозрачна оранжева нишка.',
               'Двуцветен / светещ', '#232428', accent='#ff6a2b')
    d.add('body', HEX)
    for s, W, H, tt, sp, cy in (('2027', 12, 21, 3.6, 8, -62), ('LAb', 30, 54, 8, 14, -8),
                                ('CoIn', 18, 30, 5, 10, 52)):
        lit, unlit = seg7(s, W, H, tt, sp, cy)
        d.add('flat', unlit, fill='#303137')
        d.add('accent', lit, glow=True, off=(0, 0))
    return d


@design
def d_circuit():
    d = Design('Платка',
               'LAB е разчертано като писти на електронна платка – с контактни площадки и отвори. '
               'Отпечатва се зелено + медна нишка.',
               'Двуцветен печат', '#1c6b46', accent='#e0a84a')
    lines = [
        [(-75, -45), (-75, 17), (-67, 25), (-41, 25)],
        [(-25, 25), (-25, -37), (-17, -45), (11, -45), (19, -37), (19, 25)],
        [(-25, -5), (19, -5)],
        [(35, 25), (35, -45), (64, -45), (72, -37), (72, -18), (64, -10), (35, -10)],
        [(35, -10), (67, -10), (75, -2), (75, 17), (67, 25), (35, 25)],
        # декоративни писти
        [(-41, 25), (-41, 38), (-30, 49), (-6, 49)],
        [(19, 25), (19, 34), (28, 43), (58, 43)],
        [(35, -45), (35, -56), (45, -66)],
        [(-75, -45), (-75, -52), (-63, -64), (-40, -64)],
        [(75, 17), (86, 17)],
    ]
    pads = [(-75, -45), (-41, 25), (-25, 25), (19, 25), (35, 25), (35, -45), (-6, 49), (58, 43),
            (45, -66), (-40, -64), (86, 17)]
    sc, ox, oy = 0.84, 0, -8
    P = lambda p: (p[0] * sc + ox, p[1] * sc + oy)
    tr = U([stroke([P(p) for p in l], 4.0) for l in lines])
    pd = U([circle(4.6, *P(p), 24) for p in pads])
    holes = U([circle(1.8, *P(p), 16) for p in pads])
    d.add('body', HEX)
    d.add('engraved', inset(HEX, 5).boundary.buffer(.5))
    d.add('accent', U(tr, pd).difference(holes))
    d.add('flat', holes, fill='#0d2e1e')
    chip = Polygon(chamf(-14, 60, 14, 74, 1.5))
    pins = U([box(x - 1.2, 56, x + 1.2, 78) for x in (-9, -3, 3, 9)])
    d.add('accent', pins.difference(chip))
    d.add('flat', chip, fill='#16181b')
    d.add('flat', txt('LABCOIN', 3.6, 0, 65, t=.7), fill='#f4f4ef')
    d.add('flat', txt('2027', 3.6, 0, 70, t=.7), fill='#f4f4ef')
    return d


@design
def d_maze():
    d = Design('Лабиринт',
               'Игра с топче: прокарай топчето от външния коридор през процепите до LAB в центъра. '
               'Отгоре се слага прозрачен капак.',
               'Лабиринт с топче', '#4b9b8f', accent='#ff4f4f')
    w = 1.8
    walls = [HEX.difference(inset(HEX, 3.5))]
    gaps = {74: [90], 56: [-30], 38: [150], 22: [-90]}
    for r, gl in gaps.items():
        rg = hexagon(r + w).difference(hexagon(r - w))
        for a in gl:
            dist = math.hypot(*hexpt(r, a))
            hw = math.degrees(7.5 / dist)
            wedge = Polygon([(0, 0)] + [(200 * math.cos(math.radians(a + s)), 200 * math.sin(math.radians(a + s)))
                                       for s in (-hw, hw)])
            rg = rg.difference(wedge)
        walls.append(rg)
    for r1, r2, a in ((56, 74, 30), (38, 56, -90), (22, 38, 210), (56, 74, 210), (38, 56, 30)):
        walls.append(stroke([hexpt(r1, a), hexpt(r2, a)], 2 * w, cap='flat'))
    d.add('body', HEX)
    d.add('raised', U(walls), fill='#e6f2ee')
    d.add('raised', txt('LAB', 11, 0, 0), fill='#e6f2ee')
    d.add('engraved', txt('COIN 2027', 6.5, 0, 77))
    d.add('accent', circle(5.2, 0, -75, 40), shadow=True, off=(.6, 1.2))
    d.add('flat', circle(1.6, -1.6, -76.8, 16), fill='#ffd0d0')
    return d


@design
def d_flask():
    d = Design('Колба',
               'A е лабораторна колба (Ерленмайер), в която „кипи“ течност с шестоъгълни мехурчета. '
               'Нивото на течността е чертата на A.',
               'Двуцветен печат', '#2a3d66', accent='#4fe3a0')
    pts = [(-9, -50), (-9, -22), (-32, 28), (-28, 34), (28, 34), (32, 28), (9, -22), (9, -50)]
    fl = U(stroke(pts, 7), box(-15, -57, 15, -50))
    inner = Polygon(pts).buffer(-3.6, join_style='mitre')
    wave = Polygon([(x, 4 + 2.4 * math.sin(x / 4.5)) for x in range(-40, 41, 2)] + [(40, 60), (-40, 60)])
    bubbles = [(-12, 20, 3.0), (6, 14, 2.2), (14, 25, 2.6), (-3, 27, 1.7)]
    liquid = inner.intersection(wave).difference(U([hexagon(r, x, y, rot=30) for x, y, r in bubbles]))
    floating = U([hexagon(r, x, y, rot=30).difference(hexagon(r - 1.1, x, y, rot=30))
                  for x, y, r in ((-2, -6, 2.6), (3, -18, 2.0), (-1, -30, 1.5))])
    group = U(fl, letter('L', 32, 62, -60, 3), letter('B', 34, 62, 60, 3))
    d.add('body', HEX)
    d.add('raised', group, fill='#e8ecf5')
    d.add('accent', U(liquid, floating), glow=True)
    d.add('raised', txt('2027', 9, 0, -71))
    d.add('raised', txt('COIN', 13, 0, 60))
    return d


DOT = {
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
    '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
}


def dotmatrix(s, p, cy, lit_r=.42, off_r=.2):
    cols = len(s) * 6 - 1
    on, off = [], []
    for i, ch in enumerate(s):
        for r, row in enumerate(DOT[ch]):
            for c, bit in enumerate(row):
                x = (i * 6 + c - (cols - 1) / 2) * p
                y = cy + (r - 3) * p
                (on if bit == '1' else off).append((x, y))
    return (U([circle(p * lit_r, x, y, 20) for x, y in on]),
            U([circle(p * off_r, x, y, 12) for x, y in off]))


@design
def d_dots():
    d = Design('Точкова матрица',
               'Като старо LED табло: всичко е от точки 5×7. Светещите точки са изпъкнали, '
               'а „изгасените“ – малки вдлъбнатини.',
               'Двуцветен / светещ', '#161616', accent='#ffb000')
    d.add('body', HEX)
    for s, p, cy in (('2027', 3.2, -62), ('LAB', 8.4, -8), ('COIN', 3.9, 50)):
        on, off = dotmatrix(s, p, cy)
        d.add('engraved', off)
        d.add('accent', on, glow=True, off=(.3, .6))
    return d


@design
def d_extrude():
    d = Design('3D букви',
               'LAB е изтеглено в перспектива – буквите изглеждат като обемни блокчета, '
               'които „стоят“ върху монетата.',
               'Релеф', '#3b3f8f', accent='#ffd23f')
    g = word('LAB', 138, 62, -8, -14, t=20)
    side = sweep(g, (10, 12)).difference(g)
    d.add('body', HEX)
    d.add('flat', side, fill=shade(d.accent, -.28))
    d.add('accent', g, off=(0, 0))
    d.add('raised', txt('COIN 2027', 10, 0, 64))
    return d


@design
def d_stripes():
    d = Design('Райета',
               'Оп-арт: фонът е на хоризонтални райета, буквите – на вертикални. '
               'Отблизо е шарка, отдалеч се чете LAB.',
               'Релеф / текстура', '#e9e6df', accent='#2b2b2e')
    letters = word('LAB', 160, 80, 0, -10, t=22)
    hl = U([box(-120, y - .9, 120, y + .9) for y in np.arange(-84, 46, 4.8)])
    hl = hl.intersection(inset(HEX, 5)).difference(grow(letters, 2.6))
    vl = U([box(x - .8, -120, x + .8, 120) for x in np.arange(-90, 91, 4.2)]).intersection(inset(letters, 2.4))
    d.add('body', HEX)
    d.add('engraved', hl)
    d.add('accent', letters)
    d.add('engraved', vl, on=d.accent)
    d.add('accent', txt('COIN 2027', 11, 0, 64, maxw=120))
    return d


@design
def d_topo():
    d = Design('Топографска карта',
               'Около буквите се разливат контурни линии като на карта с височини. '
               'Изглежда много добре при печат с фина дюза.',
               'Релеф / текстура', '#22325c', accent='#f6f3ea')
    letters = word('LAB', 140, 66, 0, -10, t=20)
    plaque = Polygon(chamf(-40, 54, 40, 74, 6))
    lines = U([letters.buffer(4.4 * k, quad_segs=6).boundary.buffer(.6) for k in range(1, 17)])
    lines = lines.intersection(inset(HEX, 5)).difference(grow(plaque, 3))
    d.add('body', HEX)
    d.add('raised', lines, off=(.4, .7))
    d.add('accent', letters)
    d.add('accent', plaque)
    d.add('engraved', txt('COIN 2027', 9, 0, 64, maxw=66), on=d.accent)
    return d


@design
def d_sketch():
    d = Design('Скицата, изчистена',
               'Най-близо до рисунката с молив: 2027 в удължен шестоъгълник горе, L като „<“, '
               'A с шестоъгълен отвор и отделна трапецовидна плочка, B със заострени купи, COIN с шестоъгълно O.',
               'Релеф + плочка', '#d4a92a', accent='#2b2b2e')
    banner = Polygon([(-52, -66), (-42, -80), (42, -80), (52, -66), (42, -52), (-42, -52)])
    Lg = stroke([(-50, -42), (-78, 0), (-52, 42), (-32, 42)], 14).intersection(inset(HEX, 6))
    outer = Polygon([(-34, 48), (-12, -44), (12, -44), (34, 48)])
    hole = hexagon(10, 0, -10)
    k = 22 / 92

    def lx(y):
        return -34 + (48 - y) * k
    notch = Polygon([(lx(20) + 13.5, 20), (-lx(20) - 13.5, 20), (-lx(49) - 13.5, 49), (lx(49) + 13.5, 49)])
    A = outer.difference(hole).difference(notch)
    Bg = U(stroke([(46, -44), (46, 44)], 12),
           stroke([(46, -44), (66, -44), (78, -22), (66, 0), (46, 0)], 12),
           stroke([(46, 0), (70, 0), (83, 22), (70, 44), (46, 44)], 12)).intersection(inset(HEX, 6))
    hO = hexagon(9, rot=30).difference(hexagon(5.3, rot=30))
    parts = [glyph('C', 11, 18, 3.6), hO, glyph('I', 3.6, 18, 3.6), glyph('N', 12.6, 18, 3.6)]
    x, row = 0, []
    for p in parts:
        b = p.bounds
        row.append(T(p, x - b[0], -b[1]))
        x += (b[2] - b[0]) + 3.4
    coin = center(U(row), 0, 69)
    d.add('body', HEX.difference(hole))
    d.add('engraved', banner)
    d.add('raised', txt('2027', 11, 0, -66))
    d.add('raised', U(Lg, A, Bg, coin), fill='#f4dc8c')
    d.add('accent', inset(notch, 1.4))
    return d


@design
def d_washer():
    d = Design('Гайка',
               'Монетата е като голяма гайка – с шестоъгълен отвор в средата (става и за ключодържател или '
               'нанизване на шнур). LAB горе, COIN долу, „болтове“ отстрани.',
               'Отвор / ключодържател', '#9aa3ad', accent='#3a3d44')
    hole = hexagon(28)
    d.add('body', HEX.difference(hole))
    d.add('raised', rim(4))
    d.add('raised', hexagon(36).difference(hole))
    d.add('engraved', hexagon(42).boundary.buffer(.5).difference(box(-40, -60, 40, -30)).difference(box(-40, 30, 40, 60)))
    d.add('accent', txt('LAB', 28, 0, -53))
    d.add('accent', txt('COIN', 17, 0, 49))
    d.add('raised', txt('2027', 8, 0, 69))
    for x in (-66, 66):
        d.add('raised', hexagon(7, x, 0))
        d.add('engraved', circle(3.2, x, 0, 20), on=shade(d.color, .09))
    return d


@design
def d_longshadow():
    d = Design('Дълга сянка',
               'Плосък дизайн: буквите хвърлят дълга сянка под 45° чак до ръба на монетата. '
               'Сянката е по-ниско ниво от релефа.',
               'Релеф на 3 нива', '#f2a541', accent='#fff7e6')
    lab = word('LAB', 138, 60, -6, -14, t=20)
    small = U(txt('COIN', 15, -24, 52), txt('2027', 9, 40, 52))
    allg = U(lab, small)
    sh = sweep(allg, (120, 120)).difference(allg).intersection(HEX)
    d.add('body', HEX)
    d.add('flat', sh, fill=shade(d.color, -.14))
    d.add('accent', allg)
    return d


@design
def d_cubes():
    d = Design('Кубчета',
               'Всеки „пиксел“ на LAB е малко изометрично кубче. Трите стени са в три нюанса – '
               'получава се 3D ефект, макар релефът да е плосък.',
               'Релеф / 3D илюзия', '#2b2b2e', accent='#7cbc3a')
    letters = word('LAB', 160, 84, 0, -12, t=26)
    s = 7.0
    tops, lefts, rights = [], [], []
    for r in range(-12, 13):
        for q in range(-20, 21):
            x, y = s * S3 * (q + r / 2), 1.5 * s * r
            if not letters.contains(Point(x, y)):
                continue
            v = [(x + s * .97 * math.cos(math.radians(a)), y + s * .97 * math.sin(math.radians(a)))
                 for a in (-90, -30, 30, 90, 150, 210)]
            c = (x, y)
            tops.append(Polygon([c, v[5], v[0], v[1]]))
            lefts.append(Polygon([c, v[3], v[4], v[5]]))
            rights.append(Polygon([c, v[1], v[2], v[3]]))
    d.add('body', HEX)
    d.add('flat', U(tops), fill=shade(d.accent, .14))
    d.add('flat', U(lefts), fill=d.accent)
    d.add('flat', U(rights), fill=shade(d.accent, -.18))
    d.add('accent', txt('COIN 2027', 11, 0, 64, maxw=120))
    return d


@design
def d_medal():
    d = Design('Медал',
               'Широк ръб с надписи по всяка страна (LAB, 20, 27, COIN), а в средата – голямо 27 '
               'върху фон от малки шестоъгълници.',
               'Релеф', '#b8693a', accent='#f3e2c7')
    inner = inset(HEX, 22)
    band = HEX.difference(inner)
    d.add('body', HEX)
    dots = []
    for r in range(-14, 15):
        for q in range(-16, 17):
            x, y = 7 * (q + r / 2), 7 * S3 / 2 * r
            if inset(inner, 4).contains(Point(x, y)):
                dots.append(hexagon(1.7, x, y))
    big = txt('27', 60, 0, 0, t=12)
    d.add('engraved', U(dots).difference(grow(big, 4)))
    d.add('raised', band)
    labels = {-90: 'LAB', 90: 'COIN', -150: '20', -30: '27'}
    for th in (-90, 90, -150, -30, 150, 30):
        x, y = (AP - 11) * math.cos(math.radians(th)), (AP - 11) * math.sin(math.radians(th))
        rot = th + 90 if th < 0 else th - 90
        if th in labels:
            g = txt(labels[th], 12, x, y)
        else:
            g = hexagon(4, x, y)
        d.add('engraved', Rot(g, rot, origin=(x, y)), on=shade(d.color, .09))
    d.add('accent', big)
    return d


@design
def d_twotone():
    d = Design('Две половини, два цвята',
               'Монетата е срязана по диагонал на черна и бяла половина; надписите сменят цвета си '
               'точно на разреза. Две парчета, два филамента.',
               'Пъзел, 2 части', '#2b2b2e', accent='#ece8de')
    regs = sorted(split(HEX, [[(-55, -120), (55, 120)]]), key=lambda p: p.centroid.x)
    content = U(word('LAB', 160, 76, 0, -8, t=20), txt('2027', 10, 0, -68), txt('COIN', 13, 0, 62))
    dark, light = d.color, d.accent
    d.add('tray', HEX, fill='#77736b')
    for reg, f, tf in ((regs[0], dark, light), (regs[1], light, dark)):
        p = inset(reg, GAP / 2)
        d.add('piece', p, fill=f)
        d.add('raised', content.intersection(p), fill=tf)
    return d


@design
def d_rounded():
    d = Design('lab coin, заоблени',
               'Малки букви със заоблени ъгли, подредени на два реда. Точката на i е шестоъгълник, '
               'а годината е в малка шестоъгълна значка.',
               'Релеф', '#e0578f', accent='#fff1f6')
    lab, _ = text('lab', 64, t=13, track=8)
    coin, _ = text('coin', 64, t=13, track=8, dot='hex')
    g = U(T(lab, -lab.bounds[2] / 2, -66), T(coin, -coin.bounds[2] / 2, 8))
    g = g.buffer(3.2, join_style='round').buffer(-6.4, join_style='round').buffer(3.2, join_style='round')
    g = fit(g, 150, 126, 0, -2)
    d.add('body', HEX)
    d.add('accent', g)
    badge = hexagon(12, 66, -30)
    d.add('raised', badge)
    d.add('engraved', txt('27', 9, 66, -30), on=shade(d.color, .09))
    return d


@design
def d_halftone():
    d = Design('Перфорация',
               'Монетата е надупчена с кръгли отвори – по-големи в буквите и все по-малки навън, '
               'като полутонов печат. На светло LAB „свети“ през нея.',
               'Отвори / сянка', '#22325c', accent='#f6f3ea')
    letters = word('LAB', 156, 78, 0, -12, t=22)
    region = inset(HEX, 7).intersection(box(-120, -120, 120, 44))
    p = 6.2
    holes = []
    for r in range(-20, 21):
        for q in range(-24, 25):
            x, y = p * (q + r / 2), p * S3 / 2 * r
            pt = Point(x, y)
            if not region.contains(pt):
                continue
            dist = 0 if letters.contains(pt) else letters.distance(pt)
            rr = 2.9 if dist == 0 else 1.25 * max(0.0, 1 - dist / 40)
            if rr > .5:
                holes.append(circle(rr, x, y, 16))
    d.add('body', HEX.difference(U(holes)))
    d.add('accent', txt('COIN 2027', 11, 0, 64, maxw=120))
    return d


@design
def d_totem():
    d = Design('Тотем',
               'LAB е подредено вертикално в канал по средата, а COIN и 2027 текат отстрани нагоре/надолу. '
               'Монетата може да виси на връзка.',
               'Релеф', '#1f9e89', accent='#f3efe4')
    channel = Polygon(chamf(-25, -82, 25, 82, 8)).intersection(inset(HEX, 5))
    d.add('body', HEX)
    d.add('engraved', channel)
    for ch, y in (('L', -50), ('A', 0), ('B', 50)):
        d.add('accent', letter(ch, 34, 40, 0, y))
    d.add('raised', txt('COIN', 15, -54, 0, rot=-90))
    d.add('raised', txt('2027', 15, 54, 0, rot=90))
    d.add('engraved', U(box(-36.6, -52, -35.4, 52), box(35.4, -52, 36.6, 52)))
    return d


@design
def d_liquid():
    d = Design('Мензура',
               'Буквите са кухи „съдове“, наполовина пълни с течност с мехурчета – '
               'лабораторна тема. Течността е от светеща/прозрачна нишка.',
               'Двуцветен печат', '#2b2b2e', accent='#3ee0d0')
    letters = word('LAB', 160, 82, 0, -10, t=24)
    inner = inset(letters, 4.2)
    outline = letters.difference(inner)
    wave = Polygon([(x, 2 + 2.6 * math.sin(x / 6.5)) for x in range(-100, 101, 2)] + [(100, 100), (-100, 100)])
    bub = [(-58, 18, 2.4), (-62, 8, 1.6), (4, 22, 2.2), (-6, 14, 1.4), (55, 20, 2.4), (60, 10, 1.6)]
    liquid = inner.intersection(wave).difference(U([circle(r, x, y, 16) for x, y, r in bub]))
    d.add('body', HEX)
    d.add('raised', outline)
    d.add('accent', liquid, glow=True, off=(0, 0))
    d.add('engraved', U([box(-88, y - .5, -82 if i % 2 else -84, y + .5) for i, y in enumerate(range(-24, 30, 6))]))
    d.add('raised', txt('COIN 2027', 11, 0, 64, maxw=120))
    return d


@design
def d_molecule():
    d = Design('Молекула',
               'LAB е нарисувано като химична формула: B е от два бензенови пръстена, '
               'A има пръстен вместо дупка, а COIN е „верига“ от атоми.',
               'Релеф / двуцветен', '#ece8de', accent='#2b2b2e')
    r = 17.0
    hw = r * S3 / 2
    bw = 3.4

    def hexring_lines(cx, cy):
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
               for a in (-90, -30, 30, 90, 150, 210)]
        return pts

    lx, ax, bx = -62, -1, 47.7
    bonds, atoms, doubles = [], [], []
    bonds.append(stroke([(lx, -2 * r), (lx, 2 * r), (lx + 1.6 * r, 2 * r)], bw, cap='round'))
    atoms += [(lx, -2 * r), (lx + 1.6 * r, 2 * r)]
    for cx, cy in ((ax, -r), (bx, -r), (bx, r)):
        pts = hexring_lines(cx, cy)
        bonds.append(LineString(pts + [pts[0]]).buffer(bw / 2, join_style='mitre'))
        for i in (0, 2, 4):
            p, q = np.array(pts[i]), np.array(pts[(i + 1) % 6])
            c = np.array((cx, cy))
            mid = (p + q) / 2
            n = (c - mid) / np.linalg.norm(c - mid)
            a, b = p + (q - p) * .22 + n * 4.6, q - (q - p) * .22 + n * 4.6
            doubles.append(stroke([tuple(a), tuple(b)], 2.2, cap='round'))
    pts = hexring_lines(ax, -r)
    bonds.append(stroke([pts[4], (ax - 1.5 * hw, 2 * r)], bw, cap='round'))
    bonds.append(stroke([pts[2], (ax + 1.5 * hw, 2 * r)], bw, cap='round'))
    atoms += [(ax - 1.5 * hw, 2 * r), (ax + 1.5 * hw, 2 * r)]
    bonds.append(stroke([(bx - hw, -r / 2), (bx - hw, r / 2)], bw))
    atoms += [(bx, -2 * r), (bx, 2 * r)]
    g = U(bonds, doubles)
    at = U([circle(4.2, x, y, 24) for x, y in atoms])
    d.add('body', HEX)
    d.add('accent', g)
    d.add('accent', at, fill='#d23c3c')
    cg, boxes = text('COIN', 12, t=2.6, track=12)
    cg = center(cg, 0, 62)
    off = cg.bounds[0] - boxes[0][1]
    links = U([box(off + bx1 + w1 + 2.5, 61.3, off + boxes[i + 1][1] - 2.5, 62.7)
               for i, (_, bx1, w1) in enumerate(boxes[:-1])])
    d.add('accent', U(cg, links))
    d.add('accent', txt('2027', 8, 0, -66))
    return d
