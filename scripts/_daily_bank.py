# -*- coding: utf-8 -*-
"""日常练习题库导出。题面见 _daily_units.json（变式原则，勿与考前卷原题相同）。"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNITS = json.loads(Path(__file__).with_name("_daily_units.json").read_text(encoding="utf-8"))

def export_js(out: Path | None = None) -> Path:
    out = out or ROOT / "data-daily.js"
    out.write_text(
        "window.MATH_DAILY = " + json.dumps(UNITS, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    return out

if __name__ == "__main__":
    p = export_js()
    print("wrote", p, "units", len(UNITS))
