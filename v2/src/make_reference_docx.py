"""Build v2/paper/reference.docx (pandoc style template) from pandoc's default:
Times New Roman 11 pt, 1.5 line spacing, black headings, US Letter, 1-inch
margins, continuous line numbers for review."""
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from common import V2

OUT = V2 / "paper" / "reference.docx"
FONT = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'


def main():
    tmp = Path(tempfile.mkdtemp())
    base = tmp / "default.docx"
    subprocess.run(["pandoc", "-o", str(base), "--print-default-data-file", "reference.docx"], check=True)
    zin = zipfile.ZipFile(base)
    files = {n: zin.read(n) for n in zin.namelist()}
    zin.close()

    s = files["word/styles.xml"].decode("utf-8")
    s = re.sub(r"<w:rPrDefault>.*?</w:rPrDefault>",
               f'<w:rPrDefault><w:rPr>{FONT}<w:sz w:val="22"/><w:szCs w:val="22"/>'
               '<w:lang w:val="en-GB"/></w:rPr></w:rPrDefault>', s, flags=re.S)
    s = re.sub(r"<w:pPrDefault>.*?</w:pPrDefault>",
               '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/>'
               '</w:pPr></w:pPrDefault>', s, flags=re.S)
    # Black, Times New Roman headings and title (pandoc's default is blue sans)
    s = re.sub(r"<w:color\b[^>]*/>", '<w:color w:val="000000"/>', s, flags=re.S)
    s = re.sub(r"<w:rFonts\b[^>]*w:asciiTheme=\"[^\"]+\"[^>]*/>", FONT, s, flags=re.S)
    sizes = {"Title": 32, "Heading1": 28, "Heading2": 24, "Heading3": 22}
    for sid, sz in sizes.items():
        s = re.sub(rf'(<w:style [^>]*w:styleId="{sid}".*?<w:rPr>)(.*?)(</w:rPr>)',
                   lambda m: m.group(1) + re.sub(r"<w:(?:sz|szCs|b|i|iCs)\b[^>]*/>", "", m.group(2), flags=re.S)
                   + f'<w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' + m.group(3), s, count=1, flags=re.S)
    files["word/styles.xml"] = s.encode("utf-8")

    d = files["word/document.xml"].decode("utf-8")
    sect = ('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="708" w:footer="708" w:gutter="0"/>'
            '<w:lnNumType w:countBy="1" w:restart="continuous"/></w:sectPr>')
    d = re.sub(r"<w:sectPr.*?</w:sectPr>", sect, d, flags=re.S) if "<w:sectPr" in d else d.replace("</w:body>", sect + "</w:body>")
    files["word/document.xml"] = d.encode("utf-8")

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in files.items():
            z.writestr(n, b)
    shutil.rmtree(tmp)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
