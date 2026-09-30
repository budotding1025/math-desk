# -*- coding: utf-8 -*-
"""
按上传 JPG 生成考前卷：
  - 试卷页 = 源 JPG/PNG 拆页（排版一致）
  - 另附答案页（合订在卷末，也可单独 _答案.pdf）

挂载规则：与「源卷标题」一致（你上传的第几单元练习）
  u01 ← pages u01（第一单元练习 · 大数）
  u02 ← pages u02（第二单元练习 · 角的度量）
  u03 ← pages u03（第三单元练习 · 三位数乘两位数）
  u04 ← pages u04（第四单元练习 · 数量关系）
  u05 ← pages u05（第五单元练习 · 平行四边形和梯形）

说明：人教 2022 教材在大数与角之间还有「公顷和平方千米」，
练习卷未单列上传，保留在 printables/extra-公顷和平方千米。
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "_source" / "unit-tests" / "pages-hd"
ANSWERS = ROOT / "answers"
JPEG_Q = 88

UNITS = [
    {
        "desk_id": "u01",
        "no": 1,
        "short": "大数的认识",
        "stem": "U1_四上_第一单元_大数的认识",
        "page_prefix": "u01",
        "answer_md": "U1_四上_第一单元_大数的认识-参考答案.md",
        "complete": True,
    },
    {
        "desk_id": "u02",
        "no": 2,
        "short": "角的度量",
        "stem": "U2_四上_第二单元_角的度量",
        "page_prefix": "u02",
        "answer_md": "U2_四上_第二单元_角的度量-参考答案.md",
        "complete": True,
    },
    {
        "desk_id": "u03",
        "no": 3,
        "short": "三位数乘两位数",
        "stem": "U3_四上_第三单元_三位数乘两位数_部分",
        "page_prefix": "u03",
        "answer_md": "U3-U5_部分答案与题型重难点.md",
        "answer_section": "三位数乘",
        "complete": False,
    },
    {
        "desk_id": "u04",
        "no": 4,
        "short": "数量关系",
        "stem": "U4_四上_第四单元_数量关系_部分",
        "page_prefix": "u04",
        "answer_md": "U3-U5_部分答案与题型重难点.md",
        "answer_section": "数量关系",
        "complete": False,
    },
    {
        "desk_id": "u05",
        "no": 5,
        "short": "平行四边形和梯形",
        "stem": "U5_四上_第五单元_平行四边形和梯形_部分",
        "page_prefix": "u05",
        "answer_md": "U3-U5_部分答案与题型重难点.md",
        "answer_section": "平行四边形",
        "complete": False,
    },
]


def find_pages(prefix: str) -> list[Path]:
    found = []
    for i in range(1, 9):
        png = PAGES / f"{prefix}-p{i:02d}.png"
        jpg = PAGES / "_pdf_jpg" / f"{prefix}-p{i:02d}.jpg"
        if png.exists():
            found.append(png)
        elif jpg.exists():
            found.append(jpg)
        else:
            break
    return found


def md_to_plain(md_path: Path, section_hint: str | None = None) -> str:
    if not md_path.exists():
        return "（暂无参考答案文件，待补。）"
    text = md_path.read_text(encoding="utf-8")
    if section_hint:
        parts = re.split(r"\n(?=## )", text)
        picked = [p for p in parts if section_hint in p]
        if picked:
            text = "\n".join(picked)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()[:6500]


def insert_image_page(doc: pymupdf.Document, img_path: Path) -> None:
    a4_w, a4_h = 595, 842
    margin = 14
    box = pymupdf.Rect(margin, margin, a4_w - margin, a4_h - margin)
    page = doc.new_page(width=a4_w, height=a4_h)
    tmp = PAGES / "_pdf_jpg"
    tmp.mkdir(parents=True, exist_ok=True)
    jpg = tmp / (img_path.stem + "_exam.jpg")
    Image.open(img_path).convert("RGB").save(jpg, "JPEG", quality=JPEG_Q, optimize=True)
    page.insert_image(box, filename=str(jpg), keep_proportion=True)


def insert_answer_page(doc: pymupdf.Document, title: str, body: str, page_label: str) -> None:
    a4_w, a4_h = 595, 842
    page = doc.new_page(width=a4_w, height=a4_h)
    y = 34
    page.insert_text((36, y), "数学书桌 · Math Desk", fontsize=11, color=(0.12, 0.49, 0.72))
    y += 22
    page.insert_text((36, y), f"{title} · 参考答案", fontsize=15, color=(0.1, 0.1, 0.1))
    y += 16
    page.insert_text((36, y), page_label, fontsize=9, color=(0.4, 0.4, 0.4))
    y += 12
    page.draw_line(pymupdf.Point(36, y), pymupdf.Point(a4_w - 36, y), color=(0.75, 0.85, 0.92), width=1)
    y += 10
    rect = pymupdf.Rect(36, y, a4_w - 36, a4_h - 36)
    safe = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    html = f"<div style='font-size:10.5pt;line-height:1.45;font-family:sans-serif'>{safe}</div>"
    try:
        page.insert_htmlbox(rect, html)
    except Exception:
        for line in body.splitlines():
            if y > a4_h - 40:
                page = doc.new_page(width=a4_w, height=a4_h)
                y = 40
            page.insert_text((36, y), line[:88], fontsize=9)
            y += 12


def unit_folder(short: str, desk_id: str) -> Path:
    p = ROOT / "units" / f"{desk_id}-{short}"
    p.mkdir(parents=True, exist_ok=True)
    (p / "04-考前测试" / "original").mkdir(parents=True, exist_ok=True)
    (p / "04-考前测试" / "source").mkdir(parents=True, exist_ok=True)
    return p


def build_unit(unit: dict) -> dict:
    pages = find_pages(unit["page_prefix"])
    if not pages:
        return {"id": unit["desk_id"], "ok": False, "reason": "no pages"}

    body = md_to_plain(ANSWERS / unit["answer_md"], unit.get("answer_section"))
    title = f"第{['一','二','三','四','五'][unit['no']-1]}单元 · {unit['short']}"
    n = len(pages)
    out = ROOT / "printables" / unit["desk_id"] / "04-考前测试"
    out.mkdir(parents=True, exist_ok=True)

    # 清掉旧的「待补」公顷等错挂文件
    for old in out.glob("*"):
        if old.is_file() and ("待补" in old.name or "公顷" in old.name):
            old.unlink()

    exam = out / f"{unit['stem']}.pdf"  # 试卷+答案
    q_only = out / f"{unit['stem']}_试卷.pdf"
    a_only = out / f"{unit['stem']}_答案.pdf"

    doc = pymupdf.open()
    for p in pages:
        insert_image_page(doc, p)
    insert_answer_page(doc, title, body, f"答案页（合订第 {n + 1} 页）· 也可打印单独答案 PDF")
    doc.save(exam, deflate=True, garbage=4)
    doc.close()

    docq = pymupdf.open()
    for p in pages:
        insert_image_page(docq, p)
    docq.save(q_only, deflate=True, garbage=4)
    docq.close()

    doca = pymupdf.open()
    insert_answer_page(doca, title, body, "单独答案页 · 可只打印这一页")
    doca.save(a_only, deflate=True, garbage=4)
    doca.close()

    uf = unit_folder(unit["short"], unit["desk_id"])
    orig = uf / "04-考前测试" / "original"
    for f in (exam, q_only, a_only):
        shutil.copy2(f, orig / f.name)
    # copy source page refs into units source as jpg links note
    src = uf / "04-考前测试" / "source"
    for p in pages:
        shutil.copy2(p, src / p.name)

    return {
        "id": unit["desk_id"],
        "ok": True,
        "pages": n,
        "complete": unit["complete"],
        "examPdf": f"printables/{unit['desk_id']}/04-考前测试/{unit['stem']}.pdf",
        "examQuestionsPdf": f"printables/{unit['desk_id']}/04-考前测试/{unit['stem']}_试卷.pdf",
        "examAnswerPdf": f"printables/{unit['desk_id']}/04-考前测试/{unit['stem']}_答案.pdf",
        "short": unit["short"],
        "no": unit["no"],
        "name": f"第{['一','二','三','四','五'][unit['no']-1]}单元 · {unit['short']}",
    }


def main() -> int:
    results = [build_unit(u) for u in UNITS]
    for r in results:
        print(r)
    (ROOT / "scripts" / "_exam_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
