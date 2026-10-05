"""Размери на шрифта и подравняване: текст 12 pt двустранно, заглавие 14 pt, точки (Heading 1) 13 pt."""
import re, sys, zipfile

SRC, OUT = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
x = files["word/document.xml"].decode("utf-8")
st = files["word/styles.xml"].decode("utf-8")

# заглавията на точките (стил Heading1) – 13 pt
m = re.search(r'<w:style [^>]*w:styleId="Heading1".*?</w:style>', st, re.S)
h = m.group(0)
h2 = re.sub(r'<w:sz w:val="\d+"/>', '<w:sz w:val="26"/>', h)
h2 = re.sub(r'<w:szCs w:val="\d+"/>', '<w:szCs w:val="26"/>', h2)
if '<w:sz ' not in h2:
    h2 = h2.replace("</w:rPr></w:style>", '<w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>')
st = st.replace(h, h2)

body = re.split(r'(<w:tbl>.*?</w:tbl>)', x, flags=re.S)
out = []
for part in body:
    if part.startswith("<w:tbl>"):
        out.append(part); continue
    def fix_p(pm):
        p = pm.group(0)
        txt = "".join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', p))
        if not txt:
            return p
        if txt == "ТЕХНИЧЕСКА ДОКУМЕНТАЦИЯ":             # заглавие на документа – 14 pt
            return re.sub(r'<w:sz w:val="\d+"/><w:szCs w:val="\d+"/>', '<w:sz w:val="28"/><w:szCs w:val="28"/>', p)
        if re.match(r'(Таблица|Фигура) ', txt):          # надписи – 12 pt
            return re.sub(r'<w:sz w:val="22"/><w:szCs w:val="22"/>', '<w:sz w:val="24"/><w:szCs w:val="24"/>', p)
        ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, re.S)
        if ppr and ('<w:jc ' in ppr.group(0) or '<w:pStyle' in ppr.group(0)):
            return p
        # основен текст – изрично двустранно подравняване
        if ppr:
            new = ppr.group(0).replace("<w:rPr", '<w:jc w:val="both"/><w:rPr', 1) if "<w:rPr" in ppr.group(0) \
                else ppr.group(0).replace("</w:pPr>", '<w:jc w:val="both"/></w:pPr>')
            return p.replace(ppr.group(0), new, 1)
        return re.sub(r'(<w:p(?: [^>]*)?>)', r'\1<w:pPr><w:jc w:val="both"/></w:pPr>', p, count=1)
    out.append(re.sub(r'<w:p(?: [^>]*)?>.*?</w:p>', fix_p, part, flags=re.S))
x = "".join(out)

files["word/document.xml"] = x.encode("utf-8")
files["word/styles.xml"] = st.encode("utf-8")
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, b in files.items():
        zo.writestr(n, b)
print("OK", OUT)
