# -*- coding: utf-8 -*-
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
for i in range(1, 10):
    uid = f"u{i:02d}"
    d = ROOT / "printables" / uid / "04-考前测试"
    qs = list(d.glob("*_试卷.pdf"))
    ans = list(d.glob("*_答案.pdf"))
    full = [p for p in d.glob("*.pdf") if "_试卷" not in p.name and "_答案" not in p.name]
    def info(files):
        return [(p.name, fitz.open(p).page_count, p.stat().st_size) for p in files]
    print(uid, "Q", info(qs), "A", info(ans), "F", info(full))
