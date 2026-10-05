"""Нанася реалните цени (окт. 2026) във форматирания от автора DOCX, без да пипа форматирането."""
import os, re, shutil, sys, zipfile

SRC, OUT, PIE = sys.argv[1], sys.argv[2], sys.argv[3]
z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
x = files["word/document.xml"].decode("utf-8")

def t(old, new, count=1):
    """Сменя съдържанието на <w:t> с точно този текст."""
    global x
    pat = re.compile(r'(<w:t(?: [^>]*)?>)' + re.escape(old) + r'(</w:t>)')
    x, n = pat.subn(lambda m: m.group(1) + new + m.group(2), x)
    assert n == count, (old, n)

def drop(container, marker):
    """Премахва целия <w:tr> / <w:p>, който съдържа marker."""
    global x
    i = x.index(marker)
    s = max(x.rfind(f"<{container} ", 0, i), x.rfind(f"<{container}>", 0, i))
    e = x.index(f"</{container}>", i) + len(container) + 3
    x = x[:s] + x[e:]

# --- Таблица 1: модели, производители, цени ---
# външният SSD отпада – ред 13 и описанието му; преномериране на редовете след него
drop("w:tr", ">Външен SSD Samsung T7 Shield 2 TB<")
for n in range(14, 18):
    t(f"{n}.", f"{n - 1}.")
t("Дънна платка ASUS TUF GAMING X870-PLUS WIFI", "Дънна платка ASUS TUF GAMING B850-PLUS WIFI", 2)
t("RAM Kingston FURY Beast 64 GB (2×32 GB) DDR5-6000", "RAM Kingston FURY Beast 64 GB (2×32 GB) DDR5-6000 CL36")
t("SSD Samsung 990 PRO 2 TB NVMe M.2", "SSD WD Black SN7100 2 TB NVMe M.2")
t("HDD WD Red Plus 4 TB", "HDD Seagate IronWolf 4 TB", 2)
t("Захранване Corsair RM1000x, 1000 W, 80 PLUS Gold", "Захранване Corsair RM850x, 850 W, 80 PLUS Gold")
t("Кутия Fractal Design North", "Кутия Fractal Design Focus 2", 2)
t("Монитор Dell UltraSharp U2723QE, 27&quot;, 4K", "Монитор Dell S2725QS, 27&quot;, 4K")
t("Клавиатура и мишка Logitech MX Keys S Combo", "Клавиатура и мишка Logitech Signature MK650")
t("UPS APC Back-UPS Pro BR1500MI, 1500 VA", "UPS APC Back-UPS BX1200MI, 1200 VA")
t("Абонамент Meshy AI Pro – изкуствен интелект за 3D модели, 12 месеца (12 × 19,99 €)",
  "Абонамент Meshy AI Pro – изкуствен интелект за 3D модели, 12 месеца (годишно плащане)")
t("Samsung", "SanDisk (WD_BLACK)")          # производител на ред 6 (първото срещане)
t("Western Digital", "Seagate")
t("Доставчик", "Магазинът")
for old, new in [("399,00", "359,99"), ("109,90", "68,64"), ("289,00", "175,00"), ("339,00", "949,00"),
                 ("1 320,00", "1 049,00"), ("189,90", "305,19"), ("119,90", "199,00"), ("179,90", "144,99"),
                 ("139,90", "67,55"), ("549,00", "296,04"), ("199,90", "73,85"), ("279,00", "145,00"),
                 ("299,00", "354,00"), ("229,00", "216,36"), ("239,88", "165,00"),
                 ("5 081,18", "4 612,61")]:
    t(old, new)
t("39,00", "44,00", 2)
# --- Описания ---
t(" – 12 ядра / 24 нишки (до 5,6 GHz). Оптимален баланс спрямо 9950X с 170 € по-ниска цена. Платформата AM5 осигурява възможност за бъдещ ъпгрейд.",
  " – 12 ядра / 24 нишки (до 5,6 GHz). Добър баланс между цена и производителност спрямо по-скъпия 9950X. Платформата AM5 осигурява възможност за бъдещ ъпгрейд.")
t(" – чипсет X870, поддръжка на PCIe 5.0, USB4 и Wi-Fi 7. Осигурява висока надеждност на компонентите.",
  " – чипсет B850, поддръжка на PCIe 5.0 и Wi-Fi 7. Около 200 € по-евтина от модела с X870, а липсващият USB4 не ми е нужен за 3D работата.")
t("RAM Kingston FURY Beast 64 GB DDR5-6000", "RAM Kingston FURY Beast 64 GB DDR5-6000 CL36")
t(" – 2x32 GB за работа със сложни сцени, 4K текстури и сканирани 3D обекти. Свободни 2 слота за бъдещо разширение до 128 GB.",
  " – 2x32 GB за работа със сложни сцени, 4K текстури и сканирани 3D обекти. Заради поскъпването на DDR5 паметта е вторият най-скъп компонент, но 64 GB са задължителни за тежки сцени. Свободни 2 слота за бъдещо разширение.")
t("SSD Samsung 990 PRO 2 TB", "SSD WD Black SN7100 2 TB")
t(" – бързо NVMe M.2 (до 7450 MB/s) за операционната система, програмите и работните проекти.",
  " – бързо NVMe M.2 (до 7250 MB/s) за операционната система, програмите и работните проекти. С около 50 € по-евтин от Samsung 990 PRO при почти същата скорост.")
t(" – надежден твърд диск за дългосрочно архивиране на завършени проекти и сурови файлове.",
  " – надежден твърд диск за непрекъсната работа, за архив и резервни копия на завършени проекти и сурови файлове.")
t("Захранване Corsair RM1000x", "Захранване Corsair RM850x")
t(" – 1000 W (80 PLUS Gold). Осигурява висока ефективност и резерв при пикова консумация от около 560 W.",
  " – 850 W (80 PLUS Gold). Осигурява висока ефективност и достатъчен резерв при пикова консумация от около 560 W.")
t(" – компютърна кутия с мрежест преден панел за оптимален въздушен поток и поддръжка на 360 mm радиатор.",
  " – евтина кутия с мрежест преден панел и два вентилатора за добър въздушен поток и място за 360 mm радиатор.")
t("Монитор Dell UltraSharp U2723QE 27&quot; 4K", "Монитор Dell S2725QS 27&quot; 4K")
t(" – 4K IPS Black дисплей с точна цветова възпроизвеждане за текстуриране и достатъчно площ за работния интерфейс.",
  " – 4K IPS дисплей (120 Hz, 99 % sRGB) с достатъчно точни цветове за текстуриране и голяма работна площ за интерфейса на Blender, на почти половин цена от серията UltraSharp.")
t("Logitech MX Keys S Combo", "Logitech Signature MK650")
t(" – ергономичен комплект с мишка MX Master 3S за прецизна 3D работа.",
  " – безжичен комплект клавиатура и мишка, напълно достатъчен за работа и със 125 € по-евтин от серията MX.")
t("UPS APC Back-UPS Pro 1500 VA", "UPS APC Back-UPS BX1200MI")
t(" – непрекъсваемо захранващо устройство за защита от загуба на данни при спиране на тока по време на рендериране.",
  " – 1200 VA / 650 W, покрива консумацията на компютъра и монитора и пази от загуба на данни при спиране на тока по време на рендериране.")
drop("w:p", ">Външен SSD Samsung T7 Shield 2 TB<")

# --- Финансов анализ ---
t("От общия бюджет са усвоени 5 081,18 € (108,39 %). Превишението от 393,18 € над първоначалния бюджет е отразено в коригирания финансов анализ. В Таблица 2 и Фигура 1 е представено разпределението по категории.",
  "От общия бюджет са усвоени 4 612,61 € (98,39 %). Остатъкът от 75,39 € е резерв за доставка или за промяна на цените до покупката. Поради силното поскъпване на RAM паметта и SSD устройствата през 2026 г. избрах по-евтини дънна платка, монитор, кутия и периферия, за да запазя 64 GB памет, RTX 5070 Ti и 3D скенера. В Таблица 2 и Фигура 1 е представено разпределението по категории.")
for old, new in [("3 086,50", "3 318,36"), ("60,74", "70,79"), ("1\u00a0486,80", "868,89"), ("29,26", "18,53"),
                 ("468,88", "381,36"), ("9,23", "8,13"), ("0,77", "0,94"),
                 ("-393,18", "75,39"), ("-8,39", "1,61")]:
    t(old, new)
t(" – икономията от избора на Ryzen 9 9900X и RTX 5070 Ti позволи включването на периферия като 3D скенер и UPS.",
  " – по-евтините дънна платка B850, монитор, кутия и периферия компенсират високите цени на паметта и позволиха 3D скенер, UPS и AI абонамент.")
t(" – предвидени са три нива на сигурност чрез UPS, локален архив и външен SSD.",
  " – UPS при спиране на тока и отделен HDD за архив и резервни копия.")

# --- Фигура 1: кръговата диаграма вместо празния ред „в“ ---
W = 4320000; H = int(W * 458 / 1306)
drawing = ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
  '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="501" name="Фигура 1" descr="Разпределение на бюджета"/>'
  '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
  '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
  '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="501" name="fig1.png"/><pic:cNvPicPr/></pic:nvPicPr>'
  '<pic:blipFill><a:blip r:embed="rIdFig1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
  '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
  '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (W, H, W, H)
m = re.search(r'<w:r(?: [^>]*)?>(?:(?!<w:r[ >]).)*?<w:t(?: [^>]*)?>в</w:t></w:r>', x)
assert m
x = x[:m.start()] + drawing + x[m.end():]
for ns, uri in [("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
                ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")]:
    if f'xmlns:{ns}=' not in x[:3000]:
        x = x.replace("<w:document ", f'<w:document xmlns:{ns}="{uri}" ', 1)

files["word/document.xml"] = x.encode("utf-8")
rels = files["word/_rels/document.xml.rels"].decode("utf-8")
rels = rels.replace("</Relationships>", '<Relationship Id="rIdFig1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig1.png"/></Relationships>')
files["word/_rels/document.xml.rels"] = rels.encode("utf-8")
ct = files["[Content_Types].xml"].decode("utf-8")
if 'Extension="png"' not in ct:
    ct = ct.replace("<Default ", '<Default ContentType="image/png" Extension="png"/><Default ', 1)
files["[Content_Types].xml"] = ct.encode("utf-8")
files["word/media/fig1.png"] = open(PIE, "rb").read()

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, b in files.items():
        zo.writestr(n, b)
print("OK", OUT)
