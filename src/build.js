// Генерира "Техническа документация" (DOCX) за компютърна конфигурация за 3D моделиране.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  Footer, AlignmentType, LevelFormat, PageNumber, HeadingLevel,
  WidthType, BorderStyle, ShadingType, VerticalAlign, SimpleField,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const BUILD = path.join(ROOT, "build");
const data = JSON.parse(fs.readFileSync(path.join(__dirname, "data.json"), "utf8"));

const FONT = "Times New Roman";
const CONTENT_W = 9071; // A4 (11906) − 3 cm вътрешно − 2 cm външно поле

const money = (v) => {
  const [i, d] = v.toFixed(2).split(".");
  return i.replace(/\B(?=(\d{3})+(?!\d))/g, " ") + "," + d;
};
const pct = (v) => v.toFixed(2).replace(".", ",");
const round2 = (v) => Math.round(v * 100) / 100;

const items = data.items.map((it) => ({ ...it, total: round2(it.price * it.qty) }));
const sum = (arr) => round2(arr.reduce((a, b) => a + b.total, 0));
const TOTAL = sum(items);
const RESERVE = round2(data.budget - TOTAL);
const USED = (TOTAL / data.budget) * 100;

// ---------- помощни функции ----------
const run = (r) => (typeof r === "string" ? new TextRun(r) : r);
const p = (...runs) => new Paragraph({ children: runs.map(run) });
const b = (t) => new TextRun({ text: t, bold: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const numbered = (...runs) => new Paragraph({ numbering: { reference: "items", level: 0 }, style: "ListText", children: runs.map(run) });
const bullet = (...runs) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, style: "ListText", children: runs.map(run) });

// надписи с поле SEQ: таблица – над нея, фигура – под нея
const seq = {};
const caption = (kind, text) => new Paragraph({
  style: "Caption",
  children: [
    new TextRun({ text: kind + " ", bold: true }),
    new SimpleField(`SEQ ${kind} \\* ARABIC`, String((seq[kind] = (seq[kind] || 0) + 1))),
    new TextRun({ text: ". ", bold: true }),
    new TextRun(text),
  ],
});
const figure = (file, w, h, text) => [
  new Paragraph({
    style: "Figure",
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(BUILD, file)),
      transformation: { width: w, height: h },
      altText: { title: text, description: text, name: file },
    })],
  }),
  caption("Фигура", text),
];

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
const R = AlignmentType.RIGHT, C = AlignmentType.CENTER;
const cell = (o, w) => new TableCell({
  borders,
  width: { size: w, type: WidthType.DXA },
  verticalAlign: VerticalAlign.CENTER,
  shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
  columnSpan: o.span,
  margins: { top: 30, bottom: 30, left: 80, right: 80 },
  children: [new Paragraph({
    style: "TableText",
    alignment: o.align || AlignmentType.LEFT,
    children: [new TextRun({ text: o.text, bold: !!o.bold, color: o.color })],
  })],
});
const table = (widths, head, rows) => new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({
      tableHeader: true,
      children: head.map((h, i) => cell({ text: h, bold: true, fill: "D9D9D9", align: C }, widths[i])),
    }),
    ...rows.map((r) => new TableRow({
      cantSplit: true,
      children: r.map((c, i) => {
        const o = typeof c === "object" ? c : { text: c };
        const w = o.span ? widths.slice(i, i + o.span).reduce((a, x) => a + x, 0) : widths[i];
        return cell(o, w);
      }),
    })),
  ],
});

// ---------- съдържание ----------
const header = [
  new Paragraph({ style: "TitleBig", children: [new TextRun("ТЕХНИЧЕСКА ДОКУМЕНТАЦИЯ")] }),
  new Paragraph({ style: "TitleSub", children: [new TextRun("Компютърна конфигурация за 3D моделиране по европейски проект")] }),
  new Paragraph({ style: "TitleSub", spacing: { after: 360 }, children: [new TextRun({ text: "Изготвил: [Име и фамилия], [клас]", italics: true })] }),
];

const intro = [
  h1("1. Въведение"),
  p(`Кандидатствахме по европейски проект за компютърна конфигурация и бяхме одобрени с бюджет ${money(data.budget)} €. Реших компютърът да е работна станция за 3D моделиране – моделиране и рендер в Blender, сканиране на реални предмети с 3D скенер и бързо създаване на модели с изкуствен интелект.`),
  p("За такава работа най-важни са видеокартата (рендерът и работата във viewport-а вървят на нея), много оперативна памет и бърз SSD. Затова повечето пари отидоха там, а на останалите части търсих добро съотношение между цена и качество. Всички цени са с ДДС и са взети от онлайн магазини в България през октомври 2026 г."),
];

const hardware = [
  h1("2. Хардуерни компоненти"),
  p("В таблица 1 са всички закупени неща с производителя и цената. След нея накратко обяснявам защо съм избрал всяко от тях – номерата съвпадат с таблицата."),
  caption("Таблица", "Компоненти на конфигурацията"),
  table([500, 4471, 2600, 1500], ["№", "Компонент / модел", "Производител", "Цена, €"], [
    ...items.map((it, i) => [{ text: `${i + 1}.`, align: C }, { text: it.name }, { text: it.maker }, { text: money(it.total), align: R }]),
    [{ text: "Общо:", span: 3, bold: true, align: R }, { text: money(TOTAL), bold: true, align: R }],
  ]),
  ...[
    ["Процесор AMD Ryzen 9 9900X", " – 12 ядра и 24 нишки, до 5,6 GHz. Взех го вместо Ryzen 9 9950X, защото е със 170 € по-евтин, а при рендер на видеокартата разликата почти не се усеща. Сокетът AM5 позволява по-късно да сменя само процесора."],
    ["Охладител ARCTIC Liquid Freezer III Pro 360", " – водно охлаждане с радиатор 360 mm. При дълъг рендер процесорът загрява и така не губи честота и не вдига шум."],
    ["Дънна платка ASUS TUF GAMING X870-PLUS WIFI", " – AM5, PCIe 5.0, USB4 и Wi-Fi 7. Серията TUF е направена за надеждност, а няма излишни геймърски екстри, за които да плащам."],
    ["RAM Kingston FURY Beast 64 GB DDR5-6000", " – при 3D 32 GB свършват бързо: сцени с много полигони, текстури в 4K и сканирани модели. Остават два свободни слота, ако някой ден трябват 128 GB."],
    ["Видеокарта GIGABYTE GeForce RTX 5070 Ti 16 GB", " – най-важната част. Blender Cycles рендерира през NVIDIA OptiX, а 16 GB видеопамет стигат за тежки сцени. RTX 5080 има същите 16 GB, но е с около 310 € по-скъпа за 15–20 % повече скорост. С тези пари купих 3D скенера и AI абонамента."],
    ["SSD Samsung 990 PRO 2 TB", " – NVMe до 7450 MB/s за системата, програмите и текущите проекти, които се отварят за секунди."],
    ["HDD WD Red Plus 4 TB", " – евтино място за архив на готови проекти, рендери и сканирания."],
    ["Захранване Corsair RM1000x", " – 1000 W, 80 PLUS Gold, 10 години гаранция. Системата тегли около 560 W, така че захранването работи наполовина натоварено, тихо и с резерв."],
    ["Кутия Fractal Design North", " – добро охлаждане с мрежест панел и място за радиатор 360 mm."],
    ["Монитор Dell UltraSharp U2723QE 27\" 4K", " – 4K резолюцията дава място за всички панели на Blender, а IPS Black матрицата показва точно цветовете на текстурите."],
    ["Logitech MX Keys S Combo", " – мишката MX Master 3S е удобна за дълга работа и има бутони, които настройвам за Blender."],
    ["UPS APC Back-UPS Pro 1500 VA", " – ако токът спре по време на рендер, имам време да запазя файла и да изключа нормално."],
    ["Външен SSD Samsung T7 Shield 2 TB", " – за резервни копия на проектите, за да не загубя всичко при повреда."],
    ["3D скенер Creality CR-Scan Ferret Pro", " – сканира предмети от около 15 mm до 2 m с точност до 0,1 mm и с цветна текстура. Така прехвърлям реални предмети в Blender и ги доработвам, вместо да моделирам всичко от нулата."],
    ["Windows 11 Pro", " – трябва за драйверите на видеокартата и скенера и за повечето 3D програми."],
    ["Абонамент Meshy AI Pro за 12 месеца", " – изкуствен интелект, който прави 3D модел от текст или от снимка и генерира текстури. Ползвам го за бързи чернови и предмети за фона, после ги оправям в Blender (експорт във FBX, OBJ, GLB и STL)."],
    ["Сглобяване и тестване", " – магазинът сглобява и тества компютъра, за да важи гаранцията на всички части."],
  ].map(([t, rest], i) => (i === 0
    ? new Paragraph({ numbering: { reference: "items", level: 0 }, style: "ListText", spacing: { before: 200 }, children: [b(t), new TextRun(rest)] })
    : numbered(b(t), rest))),
  p("Програмата за моделиране Blender е безплатна, затова не съм предвидил пари за нея. Офис пакет не купих, защото не е нужен за 3D работата."),
];

const cats = [...new Set(items.map((i) => i.cat))];
const finance = [
  h1("3. Финансов анализ"),
  p(`От одобрените ${money(data.budget)} € съм изхарчил ${money(TOTAL)} €, т.е. ${pct(USED)} % от бюджета. Остават ${money(RESERVE)} € за доставка или ако някоя цена се вдигне до покупката. В таблица 2 и на фигура 1 се вижда за какво отиват парите.`),
  caption("Таблица", "Разходи по категории"),
  table([4271, 2400, 2400], ["Категория", "Сума, €", "Дял от бюджета, %"], [
    ...cats.map((c) => {
      const s = sum(items.filter((i) => i.cat === c));
      return [{ text: c }, { text: money(s), align: R }, { text: pct((s / data.budget) * 100), align: R }];
    }),
    [{ text: "Остатък" }, { text: money(RESERVE), align: R }, { text: pct((RESERVE / data.budget) * 100), align: R }],
    [{ text: "Общо (бюджет)", bold: true }, { text: money(data.budget), bold: true, align: R }, { text: "100,00", bold: true, align: R }],
  ]),
  ...figure("fig2_pie.png", 360, 214, "Разпределение на бюджета"),
  p("Защо съм избрал точно тези компоненти:"),
  bullet(b("Парите са там, където има ефект"), " – видеокартата, паметта и процесорът определят колко бързо се рендерира и колко тежки сцени мога да отворя."),
  bullet(b("Спестих там, където разликата е малка"), " – RTX 5070 Ti вместо RTX 5080 и Ryzen 9 9900X вместо 9950X спестиха около 480 €. С тях купих 3D скенер, AI абонамент и UPS, които дават повече на работата, отколкото малко повече скорост."),
  bullet(b("Сигурност на данните"), " – UPS, външен SSD и отделен HDD за архив, защото един изгубен проект струва повече от тях."),

  h1("4. Заключение"),
  p("С този бюджет успях да събера пълна работна станция за 3D – мощен компютър за моделиране и рендер, 4K монитор, 3D скенер за реални предмети и AI за бързо създаване на модели. Всички части са от познати производители с гаранция от 2 до 10 години, а компютърът може да се надгради с още памет или нов процесор."),
];

// ---------- двустранен печат: номерът на страницата е от външната страна ----------
const ftr = (align) => new Footer({ children: [new Paragraph({ style: "FooterText", alignment: align, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] });

const doc = new Document({
  creator: "[Име и фамилия]",
  title: "Техническа документация – конфигурация за 3D моделиране",
  evenAndOddHeaderAndFooters: true,
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 276, after: 100 } } } },
    paragraphStyles: [
      { id: "Normal", name: "Normal", run: { font: FONT, size: 24 },
        paragraph: { alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 709 }, spacing: { line: 276, after: 100 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true },
        paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22 },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 120, line: 240 }, keepNext: true } },
      { id: "Figure", name: "Figure", basedOn: "Normal", next: "Caption",
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 0, line: 240 }, keepNext: true } },
      { id: "TableText", name: "Table Text", basedOn: "Normal", run: { font: FONT, size: 20 },
        paragraph: { indent: { firstLine: 0 }, spacing: { before: 0, after: 0, line: 240 } } },
      { id: "ListText", name: "List Text", basedOn: "Normal", paragraph: { indent: { firstLine: 0 }, spacing: { after: 60 } } },
      { id: "TitleBig", name: "Title Big", basedOn: "Normal", run: { font: FONT, size: 32, bold: true },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { after: 60 } } },
      { id: "TitleSub", name: "Title Sub", basedOn: "Normal", run: { font: FONT, size: 24 },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { after: 0 } } },
      { id: "FooterText", name: "Footer Text", basedOn: "Normal", run: { font: FONT, size: 20 },
        paragraph: { indent: { firstLine: 0 }, spacing: { after: 0, line: 240 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "items", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1069, hanging: 360 } } } }] },
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1069, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        // left = вътрешно поле, right = външно (огледалните полета се включват в settings.xml)
        margin: { top: 1134, bottom: 1134, left: 1701, right: 1134, header: 567, footer: 567 },
      },
    },
    footers: { default: ftr(AlignmentType.RIGHT), even: ftr(AlignmentType.LEFT) },
    children: [...header, ...intro, ...hardware, ...finance],
  }],
});

const out = process.argv[2] || path.join(BUILD, "raw.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`OK ${out}  total=${money(TOTAL)} reserve=${money(RESERVE)} used=${pct(USED)}%`);
});
