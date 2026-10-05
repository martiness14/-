// Генерира "Техническа документация" (DOCX) за компютърна конфигурация по европейски проект.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, LevelFormat, PageNumber, PageBreak,
  TableOfContents, WidthType, BorderStyle, ShadingType, VerticalAlign,
  SimpleField,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const BUILD = path.join(ROOT, "build");
const data = JSON.parse(fs.readFileSync(path.join(__dirname, "data.json"), "utf8"));

// ---------- помощни функции ----------
const FONT = "Times New Roman";
const CONTENT_W = 9071; // A4 (11906) − 3 cm вътрешно − 2 cm външно поле

const money = (v) => {
  const [i, d] = Math.abs(v).toFixed(2).split(".");
  return (v < 0 ? "−" : "") + i.replace(/\B(?=(\d{3})+(?!\d))/g, " ") + "," + d;
};
const pct = (v) => v.toFixed(2).replace(".", ",");
const round2 = (v) => Math.round(v * 100) / 100;

const items = data.items.map((it) => {
  const total = round2(it.price * it.qty);
  const net = round2(total / (1 + data.vat));
  return { ...it, total, net, vatSum: round2(total - net) };
});
const sum = (k, arr = items) => round2(arr.reduce((a, b) => a + b[k], 0));
const TOTAL = sum("total");
const NET = sum("net");
const VAT = sum("vatSum");
const RESERVE = round2(data.budget - TOTAL);
const USED = (TOTAL / data.budget) * 100;
const byName = (s) => items.find((i) => i.name.includes(s));

// абзац с отстъп (основен текст)
const p = (...runs) => new Paragraph({
  children: runs.map((r) => (typeof r === "string" ? new TextRun(r) : r)),
});
const b = (t) => new TextRun({ text: t, bold: true });
// абзац с удебелено начало: "Описание: ..."
const lead = (label, text) => p(b(label + " "), text);
const bullet = (...runs) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  style: "ListText",
  children: runs.map((r) => (typeof r === "string" ? new TextRun(r) : r)),
});
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });

// надписи: таблица – над нея, фигура – под нея (номерирани с поле SEQ)
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
const tableCaption = (t) => caption("Таблица", t);
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

// таблици
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
const cell = (text, w, opt = {}) => new TableCell({
  borders,
  width: { size: w, type: WidthType.DXA },
  verticalAlign: VerticalAlign.CENTER,
  shading: opt.fill ? { fill: opt.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
  columnSpan: opt.span,
  margins: { top: 50, bottom: 50, left: 90, right: 90 },
  children: [new Paragraph({
    style: "TableText",
    alignment: opt.align || AlignmentType.LEFT,
    children: [new TextRun({ text, bold: !!opt.bold, color: opt.color })],
  })],
});
const HEAD = "1F3864";
const table = (widths, head, rows, opts = {}) => new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({
      tableHeader: true,
      children: head.map((h, i) => cell(h, widths[i], { bold: true, fill: HEAD, color: "FFFFFF", align: AlignmentType.CENTER })),
    }),
    ...rows.map((r, ri) => new TableRow({
      cantSplit: true,
      children: r.map((c, i) => {
        const o = typeof c === "object" ? c : { text: c };
        return cell(o.text, o.span ? widths.slice(i, i + o.span).reduce((a, x) => a + x, 0) : widths[i], {
          align: o.align || (opts.align && opts.align[i]) || AlignmentType.LEFT,
          bold: o.bold,
          span: o.span,
          fill: o.fill || (ri % 2 ? "F2F2F2" : undefined),
        });
      }),
    })),
  ],
});
const R = AlignmentType.RIGHT, C = AlignmentType.CENTER;

// ---------- съдържание ----------
const titlePage = [
  new Paragraph({ style: "TitleSmall", children: [new TextRun("[Наименование на училището / организацията]")] }),
  new Paragraph({ style: "TitleSmall", children: [new TextRun("[Наименование и номер на проекта]")] }),
  new Paragraph({ spacing: { before: 2600 }, style: "TitleBig", children: [new TextRun("ТЕХНИЧЕСКА ДОКУМЕНТАЦИЯ")] }),
  new Paragraph({ style: "TitleSub", children: [new TextRun("на компютърна конфигурация, закупена със средства по европейски проект")] }),
  new Paragraph({ style: "TitleSub", spacing: { before: 360 }, children: [new TextRun({ text: "Обосновка на избраните хардуерни компоненти и финансов анализ на изразходваните средства", italics: true })] }),
  new Paragraph({ style: "TitleSub", spacing: { before: 600 }, children: [new TextRun({ text: `Одобрен бюджет: ${money(data.budget)} €`, bold: true })] }),
  new Paragraph({ style: "TitleInfo", spacing: { before: 3400 }, children: [new TextRun("Изготвил: [Име и фамилия]")] }),
  new Paragraph({ style: "TitleInfo", children: [new TextRun("Клас: [клас], № [номер]")] }),
  new Paragraph({ style: "TitleInfo", children: [new TextRun("Проверил: [Име на преподавателя]")] }),
  new Paragraph({ style: "TitleSmall", spacing: { before: 1200 }, children: [new TextRun("гр. [град], октомври 2026 г.")] }),
  new Paragraph({ children: [new PageBreak()] }),
];

const toc = [
  new Paragraph({ style: "TocHeading", children: [new TextRun("СЪДЪРЖАНИЕ")] }),
  new TableOfContents("Съдържание", { hyperlink: true, headingStyleRange: "1-2" }),
];

const intro = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun("1. Увод")] }),
  p(`Настоящата техническа документация е изготвена във връзка с кандидатстването по европейски проект за закупуване на компютърна конфигурация. Проектното предложение е одобрено за финансиране с бюджет в размер на ${money(data.budget)} € (с включен ДДС).`),
  p("Целта на документа е да опише избраните хардуерни компоненти и техните производители, да обоснове взетите технически решения и да представи финансов анализ на изразходваните средства, който доказва, че бюджетът е използван ефективно и по предназначение."),
  p("Конфигурацията е предвидена като високопроизводителна работна станция за компютърна графика, 3D моделиране, обработка на видео, програмиране и провеждане на онлайн обучения и видеоконференции с партньорите по проекта. Тези задачи изискват мощен многоядрен процесор, видеокарта с голяма видеопамет, голям обем оперативна памет и бързо и надеждно съхранение на данните."),

  h1("2. Изисквания към конфигурацията"),
  p("Преди избора на конкретни компоненти бяха формулирани следните изисквания, произтичащи от дейностите по проекта:"),
  bullet(b("Производителност"), " – многоядрен процесор от последно поколение за рендиране, компилиране и видеообработка."),
  bullet(b("Графична мощ"), " – видеокарта с поне 16 GB видеопамет и поддръжка на CUDA/OptiX за професионален софтуер."),
  bullet(b("Оперативна памет"), " – не по-малко от 64 GB DDR5 за работа с големи проекти и няколко приложения едновременно."),
  bullet(b("Съхранение на данни"), " – бърз NVMe SSD за системата и програмите и отделен диск с голям капацитет за архив."),
  bullet(b("Надеждност и защита"), " – качествено захранване, непрекъсваемо захранване (UPS) и външно устройство за резервни копия."),
  bullet(b("Ергономия"), " – монитор с висока резолюция и точно възпроизвеждане на цветовете, удобна клавиатура и мишка."),
  bullet(b("Легален софтуер"), " – лицензирана операционна система и офис пакет без абонаментни такси след края на проекта."),
  bullet(b("Финансова дисциплина"), ` – общата стойност да не надвишава одобрения бюджет от ${money(data.budget)} €, а всички компоненти да са с гаранция и да се предлагат от официални търговци в България.`),
  p("Цените в документа са определени след сравнение на оферти от три независими търговци на компютърна техника в България. За всеки компонент е избрана най-изгодната оферта при еднакви технически параметри и гаранционни условия."),
];

const comp = (title, desc, maker, why) => [h2(title), lead("Описание:", desc), lead("Производител:", maker), lead("Обосновка на избора:", why)];

const hardware = [
  h1("3. Хардуерни компоненти"),
  p("В тази част е представен всеки от избраните компоненти – кратко техническо описание, информация за производителя и обосновка защо е предпочетен пред алтернативите. На фигура 1 е показана блоковата схема на конфигурацията, а в таблица 1 са обобщени основните характеристики на компонентите."),
  ...figure("fig1_block.png", 560, 315, "Блокова схема на компютърната конфигурация"),
  tableCaption("Обобщение на избраните хардуерни компоненти"),
  table([1650, 2550, 1800, 3071], ["Компонент", "Модел", "Производител", "Основни характеристики"], [
    ["Процесор", "Ryzen 9 9900X", "AMD", "12 ядра / 24 нишки, до 5,6 GHz, 64 MB L3 кеш, 120 W"],
    ["Охладител", "Liquid Freezer III Pro 360", "ARCTIC", "Водно охлаждане, радиатор 360 mm, 3 вентилатора"],
    ["Дънна платка", "TUF GAMING X870-PLUS WIFI", "ASUS", "Сокет AM5, чипсет X870, PCIe 5.0, USB4, Wi-Fi 7"],
    ["Оперативна памет", "FURY Beast DDR5-6000", "Kingston", "64 GB (2 × 32 GB), CL30, AMD EXPO"],
    ["Видеокарта", "RTX 5080 WINDFORCE OC 16G", "GIGABYTE / NVIDIA", "16 GB GDDR7, архитектура Blackwell, DLSS 4"],
    ["SSD", "990 PRO 2 TB", "Samsung", "NVMe PCIe 4.0, до 7450 MB/s четене"],
    ["HDD", "WD Red Plus 4 TB", "Western Digital", "SATA 6 Gb/s, CMR, за режим 24/7"],
    ["Захранване", "RM1000x", "Corsair", "1000 W, 80 PLUS Gold, модулно, ATX 3.1"],
    ["Кутия", "North", "Fractal Design", "ATX Mid Tower, мрежест панел, 2 × 140 mm вентилатора"],
    ["Монитор", "UltraSharp U2723QE", "Dell", "27\", 3840 × 2160, IPS Black, USB-C хъб"],
    ["Клавиатура и мишка", "MX Keys S Combo", "Logitech", "Безжични, Bluetooth / Logi Bolt, презареждаеми"],
    ["Уеб камера", "Brio 500", "Logitech", "Full HD 1080p, два микрофона, капак за поверителност"],
    ["UPS", "Back-UPS Pro BR1500MI", "APC (Schneider Electric)", "1500 VA / 900 W, AVR, LCD дисплей"],
    ["Външен SSD", "T7 Shield 2 TB", "Samsung", "USB 3.2 Gen 2, до 1050 MB/s, IP65"],
  ]),

  ...comp("3.1. Процесор AMD Ryzen 9 9900X",
    "Процесорът е изграден на архитектурата Zen 5 и е произведен по 4-нанометров технологичен процес. Разполага с 12 ядра и 24 нишки, базова честота 4,4 GHz и максимална честота до 5,6 GHz, 64 MB кеш памет от трето ниво и номинална мощност (TDP) 120 W. Поддържа памет DDR5 и интерфейс PCIe 5.0, монтира се в сокет AM5.",
    "Advanced Micro Devices (AMD) е американска компания, основана през 1969 г., със седалище в Санта Клара, Калифорния. Тя е един от двата водещи световни производители на процесори за персонални компютри и сървъри, както и производител на видеокарти Radeon.",
    "Процесорът предлага много добро съотношение цена/производителност в многонишкови задачи като рендиране, видеокодиране и компилиране. Спрямо 16-ядрения Ryzen 9 9950X той е със 170 € по-евтин, а разликата в производителност за нашите задачи е около 20–25 %. Спестените средства позволиха закупуването на UPS и външен диск за резервни копия. Платформата AM5 се поддържа от AMD в дългосрочен план, което позволява бъдеща надстройка само чрез смяна на процесора."),

  ...comp("3.2. Охладителна система ARCTIC Liquid Freezer III Pro 360",
    "Затворена система за водно охлаждане (AIO) с радиатор 360 mm и три вентилатора P12 Pro. Помпата е с отместен монтаж, оптимизиран за процесорите AMD, а допълнителен малък вентилатор охлажда захранващата верига (VRM) на дънната платка.",
    "ARCTIC е европейски производител на охладителни системи, основан през 2001 г. в Швейцария, със седалище в Брауншвайг, Германия. Компанията е известна с тихи и ефективни продукти на достъпни цени.",
    "При продължително натоварване (рендиране на видео и 3D сцени) процесорът отделя значителна топлина. Водното охлаждане поддържа ниски температури и нисък шум, като не позволява понижаване на честотата поради прегряване. Моделът е сред най-добре представящите се в независими тестове при цена около 110 €."),

  ...comp("3.3. Дънна платка ASUS TUF GAMING X870-PLUS WIFI",
    "Дънна платка във формат ATX със сокет AM5 и чипсет AMD X870. Разполага с четири слота за памет DDR5, слот PCIe 5.0 x16 за видеокартата, няколко слота M.2 (включително PCIe 5.0), портове USB4, мрежова карта 2,5 Gb Ethernet, Wi-Fi 7 и Bluetooth. Захранващата верига е с усилени радиатори.",
    "ASUSTeK Computer Inc. (ASUS) е тайванска компания, основана през 1989 г., със седалище в Тайпе. Тя е един от най-големите световни производители на дънни платки, лаптопи и видеокарти.",
    "Серията TUF е предназначена за висока надеждност и издръжливост при продължителна работа. Платката поддържа всички съвременни стандарти (PCIe 5.0, USB4, Wi-Fi 7), което гарантира, че конфигурацията няма да остарее бързо. По-скъпите модели от серията ROG предлагат основно допълнителни геймърски функции, които не са необходими за целите на проекта."),

  ...comp("3.4. Оперативна памет Kingston FURY Beast 64 GB DDR5-6000",
    "Комплект от два модула по 32 GB DDR5 с честота 6000 MT/s и латентност CL30. Модулите поддържат профили AMD EXPO и Intel XMP 3.0 за автоматична настройка и са с алуминиеви охлаждащи радиатори.",
    "Kingston Technology е американска компания, основана през 1987 г., със седалище във Фаунтин Вали, Калифорния. Тя е най-големият независим производител на модули памет в света.",
    "64 GB памет позволяват едновременна работа с професионален софтуер за видео, 3D и виртуални машини без забавяне. Честотата 6000 MT/s с CL30 е оптималната комбинация за процесорите Ryzen 9000. Изборът на два модула оставя два свободни слота за бъдещо разширение до 128 GB. Kingston предоставя доживотна ограничена гаранция."),

  ...comp("3.5. Видеокарта GIGABYTE GeForce RTX 5080 WINDFORCE OC 16G",
    "Видеокартата е базирана на графичния процесор NVIDIA GeForce RTX 5080 с архитектура Blackwell. Разполага с 10 752 CUDA ядра, 16 GB видеопамет GDDR7 с 256-битова шина, тензорни ядра от пето поколение, RT ядра от четвърто поколение и поддръжка на DLSS 4. Консумацията е до 360 W, а охлаждането WINDFORCE е с три вентилатора.",
    "Графичният процесор е разработен от NVIDIA – американска компания, основана през 1993 г. в Санта Клара, Калифорния, световен лидер в графичните процесори и изкуствения интелект. Самата карта е произведена от GIGABYTE Technology – тайванска компания, основана през 1986 г., партньор на NVIDIA.",
    "Видеокартата е най-скъпият компонент, тъй като е ключова за рендиране, видеомонтаж и работа с изкуствен интелект. Технологиите CUDA и OptiX се поддържат от Blender, Adobe Premiere Pro, DaVinci Resolve и др. и ускоряват работата многократно. 16 GB видеопамет са достатъчни за сложни сцени. По-мощната RTX 5090 струва над 2 400 € и би заела повече от половината бюджет, а по-евтините алтернативи предлагат по-слаба поддръжка на професионален софтуер (виж таблица 4)."),

  ...comp("3.6. Устройства за съхранение – Samsung 990 PRO 2 TB и WD Red Plus 4 TB",
    "Samsung 990 PRO е NVMe SSD с интерфейс PCIe 4.0 x4, скорост на четене до 7450 MB/s и запис до 6900 MB/s, ресурс 1200 TBW и 5 години гаранция. WD Red Plus е 3,5-инчов твърд диск с капацитет 4 TB, технология на запис CMR и интерфейс SATA 6 Gb/s, предназначен за непрекъсната работа (24/7).",
    "Samsung Electronics е южнокорейска компания, основана през 1969 г., със седалище в Сувон – най-големият производител на флаш памет в света. Western Digital е американска компания, основана през 1970 г., със седалище в Сан Хосе, Калифорния, един от лидерите при твърдите дискове.",
    "SSD устройството осигурява бързо стартиране на системата и програмите и бързо зареждане на проекти. Твърдият диск предлага голям капацитет на ниска цена за архив на готови проекти и видеоматериали. Комбинацията от двете устройства дава най-добро съотношение между скорост, обем и цена."),

  ...comp("3.7. Захранващ блок Corsair RM1000x",
    "Захранване с мощност 1000 W, сертификат за ефективност 80 PLUS Gold, напълно модулни кабели, съответствие със стандарта ATX 3.1 и директен 12V-2x6 кабел за съвременни видеокарти. Вентилаторът е 140 mm и спира при ниско натоварване. Гаранцията е 10 години.",
    "Corsair е американска компания, основана през 1994 г., със седалище във Фримонт, Калифорния, производител на компоненти и периферия за компютри.",
    "Максималната консумация на системата е около 620 W (процесор до 160 W, видеокарта до 360 W, останалите компоненти около 100 W). Захранване от 1000 W работи при около 60 % натоварване, където ефективността е най-висока, а шумът – минимален, и оставя резерв за бъдеща надстройка. Сертификатът Gold намалява разходите за електроенергия, а 10-годишната гаранция е доказателство за качество."),

  ...comp("3.8. Кутия Fractal Design North",
    "Кутия тип ATX Mid Tower с мрежест (mesh) страничен панел и преден панел с декоративни дървени елементи. Включва два вентилатора от 140 mm, поддържа видеокарти с дължина до 355 mm и радиатор 360 mm.",
    "Fractal Design е шведска компания, основана през 2007 г., със седалище в Гьотеборг, известна със скандинавския си минималистичен дизайн.",
    "Кутията осигурява отличен въздушен поток, необходим за мощните процесор и видеокарта, побира радиатора 360 mm и е тиха. Дизайнът ѝ е подходящ за офис или учебна среда."),

  ...comp("3.9. Монитор Dell UltraSharp U2723QE",
    "27-инчов монитор с резолюция 3840 × 2160 (4K UHD) и матрица IPS Black с контраст 2000:1. Покрива 98 % от цветовото пространство DCI-P3 и 100 % от sRGB. Разполага с USB-C хъб със захранване до 90 W, LAN порт (RJ45), KVM превключвател и стойка с регулиране на височината. Технологията ComfortView Plus намалява синята светлина.",
    "Dell Technologies е американска компания, основана през 1984 г. от Майкъл Дел, със седалище в Раунд Рок, Тексас. Серията UltraSharp е професионалната линия монитори на компанията.",
    "Точното възпроизвеждане на цветовете е задължително при графичен дизайн и видеообработка. 4K резолюцията дава повече работно пространство, а ергономичната стойка намалява умората при продължителна работа. Dell предлага 3 години гаранция с бърза подмяна."),

  ...comp("3.10. Периферни устройства",
    "Комплектът Logitech MX Keys S Combo включва безжична клавиатура MX Keys S, мишка MX Master 3S (сензор 8000 DPI, тихи бутони) и подложка за китката. Уеб камерата Logitech Brio 500 заснема видео Full HD 1080p, има автоматична корекция на светлината, два микрофона с шумопотискане и капак за поверителност. Външният SSD Samsung T7 Shield 2 TB е с интерфейс USB 3.2 Gen 2, скорост до 1050 MB/s и защита от прах и вода IP65.",
    "Logitech International е швейцарска компания, основана през 1981 г., със седалище в Лозана – световен лидер в компютърната периферия. Samsung Electronics е представена в т. 3.6.",
    "Ергономичните клавиатура и мишка повишават продуктивността и намаляват натоварването на ръцете. Уеб камерата е необходима за онлайн срещите с партньорите по проекта. Външният SSD е предназначен за редовни резервни копия на важните данни, съхранявани отделно от компютъра."),

  ...comp("3.11. Непрекъсваемо захранване APC Back-UPS Pro BR1500MI",
    "Линейно-интерактивен UPS с мощност 1500 VA / 900 W, автоматично регулиране на напрежението (AVR), синусоидален изход, LCD дисплей и USB връзка със софтуера PowerChute за автоматично безопасно изключване на компютъра.",
    "APC е създадена през 1981 г. в САЩ и от 2007 г. е част от френската група Schneider Electric със седалище в Рюей-Малмезон – световен лидер в енергийното управление.",
    "UPS-ът защитава скъпото оборудване от токови удари и колебания в мрежата и предотвратява загуба на незапазена работа при спиране на тока. Мощността 900 W покрива максималната консумация на компютъра и монитора (около 660 W)."),

  h2("3.12. Софтуер"),
  lead("Описание:", "Операционна система Microsoft Windows 11 Pro и офис пакет Microsoft Office Home 2024 (Word, Excel, PowerPoint и OneNote) с безсрочен лиценз."),
  lead("Производител:", "Microsoft Corporation е американска компания, основана през 1975 г. от Бил Гейтс и Пол Алън, със седалище в Редмънд, Вашингтон."),
  lead("Обосновка на избора:", "Версията Pro включва криптиране на диска BitLocker, виртуализация Hyper-V, отдалечен работен плот и групови политики, необходими в учебна или организационна среда. Офис пакетът е с еднократно плащане, а не с абонамент, така че след приключване на проекта няма да има допълнителни разходи. Използването на лицензиран софтуер е задължително условие при проекти с европейско финансиране."),
];

// ---------- финансов анализ ----------
const cats = [...new Set(items.map((i) => i.cat))];
const finance = [
  h1("4. Финансов анализ на изразходваните средства"),
  h2("4.1. Количествено-стойностна сметка"),
  p(`В таблица 2 са представени всички закупени позиции с цена без ДДС, начислен ДДС (${data.vat * 100} %) и обща стойност. Общата стойност на конфигурацията е ${money(TOTAL)} €, от които ${money(NET)} € без ДДС и ${money(VAT)} € ДДС.`),
  tableCaption("Количествено-стойностна сметка на закупените компоненти"),
  table([500, 4050, 600, 1300, 1150, 1471],
    ["№", "Наименование", "Бр.", "Цена без ДДС, €", "ДДС, €", "Стойност с ДДС, €"],
    [
      ...items.map((it, i) => [{ text: `${i + 1}.`, align: C }, it.name, { text: String(it.qty), align: C }, { text: money(it.net), align: R }, { text: money(it.vatSum), align: R }, { text: money(it.total), align: R }]),
      [{ text: "ОБЩО:", span: 3, bold: true, align: R, fill: "D9E2F3" }, { text: money(NET), bold: true, align: R, fill: "D9E2F3" }, { text: money(VAT), bold: true, align: R, fill: "D9E2F3" }, { text: money(TOTAL), bold: true, align: R, fill: "D9E2F3" }],
      [{ text: "Одобрен бюджет:", span: 5, align: R }, { text: money(data.budget), align: R }],
      [{ text: "Остатък (резерв):", span: 5, bold: true, align: R }, { text: money(RESERVE), bold: true, align: R }],
    ]),

  h2("4.2. Разпределение на средствата по категории"),
  p(`Разходите са групирани в четири категории (таблица 3 и фигура 2). Най-голям дял заема системният блок, което е логично, тъй като той определя производителността на работната станция. Неизразходваният остатък е само ${money(RESERVE)} €, т.е. бюджетът е усвоен на ${pct(USED)} %.`),
  tableCaption("Разпределение на разходите по категории"),
  table([3271, 1500, 2150, 2150], ["Категория", "Брой позиции", "Сума с ДДС, €", "Дял от бюджета, %"], [
    ...cats.map((c) => {
      const arr = items.filter((i) => i.cat === c);
      const s = sum("total", arr);
      return [c, { text: String(arr.length), align: C }, { text: money(s), align: R }, { text: pct((s / data.budget) * 100), align: R }];
    }),
    ["Резерв (неизразходвани средства)", { text: "–", align: C }, { text: money(RESERVE), align: R }, { text: pct((RESERVE / data.budget) * 100), align: R }],
    [{ text: "ОБЩО", bold: true, fill: "D9E2F3" }, { text: String(items.length), bold: true, align: C, fill: "D9E2F3" }, { text: money(data.budget), bold: true, align: R, fill: "D9E2F3" }, { text: "100,00", bold: true, align: R, fill: "D9E2F3" }],
  ]),
  ...figure("fig2_pie.png", 540, 320, "Разпределение на бюджета по категории разходи"),

  h2("4.3. Стойност по компоненти"),
  p(`На фигура 3 компонентите са подредени по стойност. Видеокартата е най-голямото единично перо – ${money(byName("RTX 5080").total)} € (${pct((byName("RTX 5080").total / data.budget) * 100)} % от бюджета), следвана от монитора и процесора. Тези три компонента формират ${pct(((byName("RTX 5080").total + byName("U2723QE").total + byName("9900X").total) / data.budget) * 100)} % от бюджета и са пряко свързани с основните дейности по проекта – графика, видео и 3D.`),
  ...figure("fig3_bars.png", 560, 378, "Стойност на компонентите с ДДС, подредени по цена"),

  h2("4.4. Сравнение с алтернативни решения – защо сме избрали тези компоненти"),
  p("За най-скъпите компоненти бяха разгледани по няколко алтернативи. Сравнението е представено в таблица 4. Избраните модели не са най-евтините, но предлагат най-доброто съотношение между цена, производителност и надеждност в рамките на бюджета."),
  tableCaption("Сравнение на избраните компоненти с алтернативи"),
  table([1350, 2150, 1100, 3271, 1200], ["Компонент", "Разгледан вариант", "Цена, €", "Оценка", "Решение"], [
    ["Процесор", "AMD Ryzen 9 9900X", { text: "399,00", align: R }, "12 ядра, ниска консумация, платформа AM5 с възможност за надстройка", { text: "Избран", bold: true, align: C }],
    ["", "AMD Ryzen 9 9950X", { text: "569,00", align: R }, "16 ядра, но +170 € – бюджетът не би стигнал за UPS и архивиране", { text: "Отхвърлен", align: C }],
    ["", "Intel Core Ultra 9 285K", { text: "≈ 579,00", align: R }, "Сходна производителност, по-висока цена, ограничена надстройка на платформата", { text: "Отхвърлен", align: C }],
    ["Видеокарта", "NVIDIA RTX 5080 16 GB", { text: "1 189,00", align: R }, "CUDA/OptiX, 16 GB GDDR7, отлична поддръжка на професионален софтуер", { text: "Избран", bold: true, align: C }],
    ["", "AMD Radeon RX 9070 XT 16 GB", { text: "≈ 699,00", align: R }, "По-евтина, но без CUDA – по-бавна в Blender и AI инструменти", { text: "Отхвърлен", align: C }],
    ["", "NVIDIA RTX 5090 32 GB", { text: "≈ 2 499,00", align: R }, "Най-мощна, но над 50 % от бюджета", { text: "Отхвърлен", align: C }],
    ["Монитор", "Dell U2723QE 27\" 4K", { text: "549,00", align: R }, "IPS Black, 98 % DCI-P3, USB-C хъб с LAN, 3 г. гаранция", { text: "Избран", bold: true, align: C }],
    ["", "LG 27UP850N 27\" 4K", { text: "≈ 349,00", align: R }, "По-евтин, но с по-нисък контраст и без LAN порт и KVM", { text: "Отхвърлен", align: C }],
  ]),
  p("Основните критерии, по които са избрани компонентите, са:"),
  bullet(b("Съотношение цена/производителност"), " – предпочетени са модели, при които допълнителната цена носи реална полза за дейностите по проекта."),
  bullet(b("Надеждност и гаранция"), " – всички компоненти са от утвърдени световни производители с гаранция от 2 до 10 години."),
  bullet(b("Енергийна ефективност"), " – процесор със 120 W TDP и захранване с 80 PLUS Gold намаляват разходите за ток през целия срок на експлоатация."),
  bullet(b("Възможност за надстройка"), " – платформа AM5, свободни слотове за памет и резерв от мощност на захранването."),
  bullet(b("Липса на последващи разходи"), " – софтуер с безсрочен лиценз, без абонаменти след края на проекта."),

  h2("4.5. Оценка на усвояването на бюджета"),
  p(`От одобрения бюджет от ${money(data.budget)} € са изразходвани ${money(TOTAL)} €, което представлява ${pct(USED)} % усвояване. Остатъкът от ${money(RESERVE)} € е по-малък от 0,5 % и може да покрие евентуални разходи за доставка или малки ценови разлики към датата на покупката.`),
  p("ДДС е включен в бюджета като допустим разход, тъй като бенефициентът (училище или организация с нестопанска цел) няма право на данъчен кредит и не може да възстанови платения данък. Всички разходи са документално обосновани с оферти и ще бъдат доказани с фактури и приемо-предавателни протоколи."),
];

const conclusion = [
  h1("5. Заключение и обосновка на взетите решения"),
  p("Избраната конфигурация напълно отговаря на изискванията на проекта. Тя съчетава висока производителност, надеждност и ергономия, като се вписва в одобрения бюджет. Основните взети решения могат да се обобщят така:"),
  bullet("Средствата са съсредоточени в компонентите с най-голямо влияние върху работата – видеокарта, процесор и памет."),
  bullet("Предпочетен е процесор с 12 ядра вместо 16, което освободи средства за защита на данните и оборудването (UPS и външен SSD)."),
  bullet("Избрани са компоненти от водещи световни производители с дълга гаранция, което намалява риска от повреди и допълнителни разходи."),
  bullet("Конфигурацията е подготвена за бъдеща надстройка без смяна на основните компоненти."),
  bullet(`Бюджетът е усвоен на ${pct(USED)} % при пълна прозрачност на разходите.`),
  p("С тази конфигурация екипът на проекта разполага с модерна работна станция, която ще се използва ефективно поне 5–6 години и ще допринесе за постигане на целите на проекта."),

  h1("6. Използвани източници"),
  ...[
    "AMD – официален сайт, спецификация на Ryzen 9 9900X: www.amd.com",
    "ARCTIC – официален сайт, Liquid Freezer III Pro 360: www.arctic.de",
    "ASUS – официален сайт, TUF GAMING X870-PLUS WIFI: www.asus.com",
    "Kingston – официален сайт, FURY Beast DDR5: www.kingston.com",
    "NVIDIA – GeForce RTX 5080: www.nvidia.com; GIGABYTE: www.gigabyte.com",
    "Samsung Semiconductor – 990 PRO и T7 Shield: semiconductor.samsung.com",
    "Western Digital – WD Red Plus: www.westerndigital.com",
    "Corsair – RM1000x: www.corsair.com",
    "Fractal Design – North: www.fractal-design.com",
    "Dell – UltraSharp U2723QE: www.dell.com",
    "Logitech – MX Keys S Combo и Brio 500: www.logitech.com",
    "APC by Schneider Electric – Back-UPS Pro BR1500MI: www.apc.com",
    "Microsoft – Windows 11 Pro и Office 2024: www.microsoft.com",
    "Оферти от търговци на компютърна техника в България, октомври 2026 г.",
  ].map((s) => new Paragraph({ numbering: { reference: "sources", level: 0 }, style: "ListText", children: [new TextRun(s)] })),
];

// ---------- колонтитули (двустранен печат: номерът е на външната страна) ----------
const HDR_TEXT = "Техническа документация – компютърна конфигурация";
const hdr = (align) => new Header({ children: [new Paragraph({ style: "HeaderText", alignment: align, children: [new TextRun(HDR_TEXT)] })] });
const ftr = (align) => new Footer({ children: [new Paragraph({ style: "FooterText", alignment: align, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] });
const empty = () => new Header({ children: [new Paragraph("")] });
const emptyF = () => new Footer({ children: [new Paragraph("")] });

// ---------- документ ----------
const doc = new Document({
  creator: "[Име и фамилия]",
  title: "Техническа документация – компютърна конфигурация",
  description: "Обосновка на хардуерните компоненти и финансов анализ",
  evenAndOddHeaderAndFooters: true,
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 360, after: 120 } } },
    },
    paragraphStyles: [
      { id: "Normal", name: "Normal", run: { font: FONT, size: 24 },
        paragraph: { alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 709 }, spacing: { line: 360, after: 120 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F3864" },
        paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { before: 360, after: 200, line: 276 }, keepNext: true, keepLines: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "2F5597" },
        paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { before: 280, after: 120, line: 276 }, keepNext: true, keepLines: true, outlineLevel: 1 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22 },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 200, line: 240 }, keepNext: false } },
      { id: "Figure", name: "Figure", basedOn: "Normal", next: "Caption",
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 200, after: 0, line: 240 }, keepNext: true } },
      { id: "TableText", name: "Table Text", basedOn: "Normal",
        run: { font: FONT, size: 20 },
        paragraph: { indent: { firstLine: 0 }, spacing: { before: 0, after: 0, line: 240 } } },
      { id: "ListText", name: "List Text", basedOn: "Normal",
        paragraph: { indent: { firstLine: 0 }, spacing: { after: 60 } } },
      { id: "TocHeading", name: "TOC Heading Custom", basedOn: "Normal",
        run: { font: FONT, size: 32, bold: true, color: "1F3864" },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { after: 360 } } },
      { id: "TitleBig", name: "Title Big", basedOn: "Normal",
        run: { font: FONT, size: 44, bold: true, color: "1F3864" },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { after: 240 } } },
      { id: "TitleSub", name: "Title Sub", basedOn: "Normal",
        run: { font: FONT, size: 28 },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 } } },
      { id: "TitleSmall", name: "Title Small", basedOn: "Normal",
        run: { font: FONT, size: 24 },
        paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { after: 0 } } },
      { id: "TitleInfo", name: "Title Info", basedOn: "Normal",
        run: { font: FONT, size: 24 },
        paragraph: { alignment: AlignmentType.LEFT, indent: { left: 5103, firstLine: 0 }, spacing: { after: 0 } } },
      { id: "HeaderText", name: "Header Text", basedOn: "Normal",
        run: { font: FONT, size: 18, italics: true, color: "595959" },
        paragraph: { indent: { firstLine: 0 }, spacing: { after: 0, line: 240 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6", space: 2 } } } },
      { id: "FooterText", name: "Footer Text", basedOn: "Normal",
        run: { font: FONT, size: 20 },
        paragraph: { indent: { firstLine: 0 }, spacing: { after: 0, line: 240 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1069, hanging: 360 } } } }] },
      { reference: "sources", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 709, hanging: 425 } } } }] },
    ],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 11906, height: 16838 }, // A4
        // left = вътрешно поле, right = външно (огледални полета се включват в settings.xml)
        margin: { top: 1418, bottom: 1418, left: 1701, right: 1134, header: 709, footer: 709 },
      },
    },
    headers: { first: empty(), default: hdr(AlignmentType.RIGHT), even: hdr(AlignmentType.LEFT) },
    footers: { first: emptyF(), default: ftr(AlignmentType.RIGHT), even: ftr(AlignmentType.LEFT) },
    children: [...titlePage, ...toc, ...intro, ...hardware, ...finance, ...conclusion],
  }],
});

const out = process.argv[2] || path.join(BUILD, "raw.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`OK ${out}  total=${money(TOTAL)} net=${money(NET)} vat=${money(VAT)} reserve=${money(RESERVE)} used=${pct(USED)}%`);
});
