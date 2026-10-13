#!/usr/bin/env python3
"""Генерира svg/NN-*.svg и index.html (галерия) за всички концепции.

    python3 labcoin-2027/build.py
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from geom import render  # noqa: E402
from designs import DESIGNS  # noqa: E402

GROUPS = [
    (0, 'A · LAB запълва монетата'),
    (7, 'B · Пъзели от парчета'),
    (17, 'C · Текстури и техники'),
]


def main():
    only = set(sys.argv[1:])
    os.makedirs(os.path.join(HERE, 'svg'), exist_ok=True)
    cards = []
    for i, fn in enumerate(DESIGNS, 1):
        slug = re.sub(r'^d_', '', fn.__name__).replace('_', '-')
        name = f'{i:02d}-{slug}.svg'
        if only and slug not in only and str(i) not in only:
            continue
        d = fn()
        svg = render(d, i)
        with open(os.path.join(HERE, 'svg', name), 'w', encoding='utf-8') as f:
            f.write(svg)
        cards.append((i, name, d))
        print(f'{i:02d} {d.title}')
    if only:
        return
    write_gallery(cards)


def write_gallery(cards):
    sections = []
    starts = {g[0]: g[1] for g in GROUPS}
    body = []
    for idx, (i, name, d) in enumerate(cards):
        if idx in starts:
            if body:
                body.append('</div>')
            body.append(f'<h2>{html.escape(starts[idx])}</h2><div class="grid">')
        body.append(
            f'<figure class="card"><div class="img"><img src="svg/{name}" alt="{html.escape(d.title)}" loading="lazy"></div>'
            f'<figcaption><div class="row"><span class="num">{i:02d}</span>'
            f'<span class="tag">{html.escape(d.mech)}</span></div>'
            f'<h3>{html.escape(d.title)}</h3><p>{html.escape(d.desc)}</p></figcaption></figure>')
    body.append('</div>')
    page = TEMPLATE.replace('{{BODY}}', '\n'.join(body)).replace('{{N}}', str(len(cards)))
    with open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page)


TEMPLATE = '''<!doctype html>
<html lang="bg"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LabCoin 2027 концепции</title>
<style>
:root{--bg:#f4f2ee;--card:#fff;--ink:#1d1d1f;--mute:#6b6b70;--line:#e4e1da;--tag:#eef6f3;--tagink:#17705f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151517;--card:#1f1f22;--ink:#f1f0ec;--mute:#a3a3a8;--line:#2e2e33;--tag:#1d322d;--tagink:#7fdcc4}}
:root[data-theme="dark"]{--bg:#151517;--card:#1f1f22;--ink:#f1f0ec;--mute:#a3a3a8;--line:#2e2e33;--tag:#1d322d;--tagink:#7fdcc4}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1240px;margin:0 auto;padding:32px 16px 64px}
header h1{font-size:30px;margin:0 0 6px;letter-spacing:-.01em}
header p{margin:0;color:var(--mute);max-width:720px}
h2{font-size:17px;margin:40px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.card{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}
.img{background:radial-gradient(circle at 50% 40%,#ffffff 0,#ebe8e2 75%);aspect-ratio:1/1;display:flex;align-items:center;justify-content:center}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .img{background:radial-gradient(circle at 50% 40%,#3a3a40 0,#232327 75%)}}
:root[data-theme="dark"] .img{background:radial-gradient(circle at 50% 40%,#3a3a40 0,#232327 75%)}
.img img{width:92%;height:92%;object-fit:contain}
figcaption{padding:12px 14px 16px}
.row{display:flex;justify-content:space-between;align-items:center;gap:8px}
.num{font:600 13px/1 ui-monospace,Menlo,monospace;color:var(--mute)}
.tag{font-size:12px;background:var(--tag);color:var(--tagink);padding:3px 8px;border-radius:99px;white-space:nowrap}
h3{font-size:16px;margin:8px 0 4px}
figcaption p{margin:0;color:var(--mute);font-size:13.5px}
</style></head><body><main>
<header><h1>LabCoin 2027 — {{N}} концепции</h1>
<p>Шестоъгълна монета с плосък връх, като 2026. Всичко е векторно (SVG) и генерирано от <code>build.py</code>,
така че размерите и дебелините лесно се сменят. Цветовете са примерни филаменти.</p></header>
{{BODY}}
</main></body></html>
'''

if __name__ == '__main__':
    main()
