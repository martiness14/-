"""Генерира фигурите за техническата документация."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "build")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "Liberation Serif"
plt.rcParams["font.size"] = 12.5

d = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
items = d["items"]
COLORS = {"Системен блок": "#2F5597", "Периферия": "#548235", "Софтуер": "#BF8F00", "Услуги": "#7F7F7F"}

# Фигура 1 – блокова схема на конфигурацията
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")

def box(x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=color, ec="#1F1F1F", lw=0.8, alpha=0.92))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color="white", fontsize=11.5, wrap=True)

def line(x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color="#404040", lw=1)

# централна дънна платка
W = 21
box(33, 25, 34, 11, "Дънна платка\nASUS TUF X870-PLUS WIFI", "#1F3864")
BLUE, GREEN = "#2F5597", "#548235"
box(2, 47, W, 9, "Процесор\nRyzen 9 9900X", BLUE)
box(27, 47, W, 9, "RAM 64 GB\nDDR5-6000", BLUE)
box(52, 47, W, 9, "Видеокарта\nRTX 5080 16 GB", BLUE)
box(77, 47, W, 9, "Монитор\nDell 27\" 4K", GREEN)
box(2, 26, W + 4, 9, "SSD 2 TB (M.2)\nSamsung 990 PRO", BLUE)
box(73, 26, W + 4, 9, "HDD 4 TB (SATA)\nWD Red Plus", BLUE)
box(2, 5, W, 9, "UPS\nAPC 1500 VA", GREEN)
box(39.5, 5, W, 9, "Захранване\nCorsair 1000 W", BLUE)
box(73, 5, W + 4, 9, "USB: клавиатура, мишка,\nкамера, външен SSD", GREEN)
line(12.5, 47, 40, 36); line(37.5, 47, 45, 36); line(62.5, 47, 58, 36)
line(73, 51.5, 77, 51.5)
line(27, 30.5, 33, 30.5); line(67, 30.5, 73, 30.5)
line(23, 9.5, 39.5, 9.5); line(50, 14, 50, 25); line(85.5, 14, 64, 25)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig1_block.png")); plt.close()

# Фигура 2 – разпределение на средствата по категории
cats = {}
for i in items:
    cats[i["cat"]] = cats.get(i["cat"], 0) + i["price"] * i["qty"]
reserve = d["budget"] - sum(cats.values())
labels = list(cats) + ["Резерв"]
vals = list(cats.values()) + [reserve]
cols = [COLORS[c] for c in cats] + ["#D9D9D9"]
fig, ax = plt.subplots(figsize=(6, 4.2), dpi=200)
wedges, _ = ax.pie(vals, colors=cols, startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5))
ax.text(0, 0, f"{d['budget']:,.0f} €".replace(",", " "), ha="center", va="center", fontsize=18, fontweight="bold")
leg = [f"{l} – {v:,.2f} € ({v / d['budget'] * 100:.1f} %)".replace(",", " ").replace(".", ",") for l, v in zip(labels, vals)]
ax.legend(wedges, leg, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=14)
ax.set_aspect("equal")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig2_pie.png"), bbox_inches="tight"); plt.close()

# Фигура 3 – стойност по компоненти
srt = sorted(items, key=lambda i: i["price"] * i["qty"])
fig, ax = plt.subplots(figsize=(8, 5.4), dpi=200)
vals = [i["price"] * i["qty"] for i in srt]
bars = ax.barh([i["short"] for i in srt], vals, color=[COLORS[i["cat"]] for i in srt])
for b, v in zip(bars, vals):
    ax.text(v + 12, b.get_y() + b.get_height() / 2, f"{v:,.2f} €".replace(",", " ").replace(".", ","), va="center", fontsize=11)
ax.set_xlabel("Цена с ДДС, €")
ax.set_xlim(0, max(vals) * 1.22)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#E0E0E0", lw=0.6); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig3_bars.png")); plt.close()
print("ok")
