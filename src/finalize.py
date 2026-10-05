"""Довършва документа: огледални полета (двустранен печат), обновяване на съдържанието и PDF."""
import os, re, subprocess, tempfile, time, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "..", "build")
OUT = os.path.abspath(os.path.join(HERE, ".."))
NAME = "Техническа_документация"
raw = os.path.join(BUILD, "raw.docx")
docx = os.path.join(OUT, NAME + ".docx")
pdf = os.path.join(OUT, NAME + ".pdf")

# 1) <w:mirrorMargins/> + bg език в settings.xml
with zipfile.ZipFile(raw) as zin, zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        buf = zin.read(item.filename)
        if item.filename == "word/settings.xml":
            s = buf.decode("utf-8")
            if "mirrorMargins" not in s:
                s = s.replace("<w:evenAndOddHeaders", "<w:mirrorMargins/><w:evenAndOddHeaders", 1)
            buf = s.encode("utf-8")
        if item.filename in ("word/styles.xml", "word/document.xml"):
            s = buf.decode("utf-8")
            # изрично правило за междуредие (без него LibreOffice изрязва изображенията)
            s = re.sub(r'<w:spacing((?:(?!w:lineRule)[^>])*?w:line="\d+"(?:(?!w:lineRule)[^>])*?)/>', r'<w:spacing\1 w:lineRule="auto"/>', s)
            if item.filename == "word/document.xml":
                n = iter(range(1, 10000))
                s = re.sub(r'<wp:docPr id="\d+"', lambda m: f'<wp:docPr id="{next(n)}"', s)
            buf = s.encode("utf-8")
        if item.filename == "word/styles.xml":
            s = buf.decode("utf-8")
            s = s.replace("<w:rPrDefault><w:rPr>", '<w:rPrDefault><w:rPr><w:lang w:val="bg-BG" w:eastAsia="en-US" w:bidi="ar-SA"/>', 1)
            buf = s.encode("utf-8")
        zout.writestr(item, buf)

# 2) LibreOffice: обновяване на полетата/съдържанието и експорт в PDF
import uno
from com.sun.star.beans import PropertyValue

def prop(n, v):
    x = PropertyValue(); x.Name = n; x.Value = v; return x

port = 2002
profile = tempfile.mkdtemp(prefix="lo_profile_")
proc = subprocess.Popen(["soffice", f"-env:UserInstallation=file://{profile}", "--headless", "--invisible", "--norestore",
                         f"--accept=socket,host=localhost,port={port};urp;"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(60):
        try:
            ctx = resolver.resolve(f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext"); break
        except Exception:
            time.sleep(0.5)
    desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    d = desktop.loadComponentFromURL(uno.systemPathToFileUrl(docx), "_blank", 0, (prop("Hidden", True),))
    d.getTextFields().refresh()
    idx = d.getDocumentIndexes()
    for _ in range(2):
        for i in range(idx.getCount()):
            idx.getByIndex(i).update()
        d.getTextFields().refresh()
    d.storeToURL(uno.systemPathToFileUrl(pdf), (prop("FilterName", "writer_pdf_Export"),))
    d.close(True)
finally:
    proc.terminate()
    proc.wait(timeout=30)
print("OK", docx, pdf)
