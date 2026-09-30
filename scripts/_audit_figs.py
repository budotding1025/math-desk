# -*- coding: utf-8 -*-
from pathlib import Path
import json
import re

try:
    import fitz
except ImportError:
    fitz = None

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "printables" / "_diagrams"

print("=== PDF images ===")
if fitz:
    for u in ["u01", "u02", "u03", "u04", "u05"]:
        pdfs = list((ROOT / "printables" / u / "04-考前测试").glob("*.pdf"))
        if not pdfs:
            print(u, "NO PDF")
            continue
        doc = fitz.open(pdfs[0])
        n = sum(len(p.get_images()) for p in doc)
        print(f"{u}: {n} images, {doc.page_count} pages, size={pdfs[0].stat().st_size}")

src = (ROOT / "scripts" / "gen_exam_clean.py").read_text(encoding="utf-8")
imgs = re.findall(r'DIAG\s*/\s*"([^"]+)"', src)
print("=== exam refs", len(imgs), "===")
miss = [n for n in imgs if not (DIAG / n).exists()]
print("missing:", miss or "none")

t = (ROOT / "data-daily.js").read_text(encoding="utf-8")
m = re.search(r"window\.MATH_DAILY = (.*);", t, re.S)
data = json.loads(m.group(1))
dm = []
n = 0
for u in data:
    for k in ("calc", "key", "app"):
        for it in u[k]["items"]:
            if isinstance(it, dict) and it.get("img"):
                n += 1
                if not (ROOT / it["img"]).exists():
                    dm.append(it["img"])
print("=== daily figures", n, "missing", dm or "none")
print("=== jpg count", len(list(DIAG.glob("*.jpg"))))
# flag scan-crop style names still used
for name in sorted(DIAG.glob("*_hd.jpg")):
    print("hd crop:", name.name, name.stat().st_size)
