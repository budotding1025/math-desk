# -*- coding: utf-8 -*-
"""Build midterm A/D clear Word+PDF from TRANSCRIPT.md (exam-from-photo)."""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

import pymupdf
import win32com.client
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_exam_a4_word import docx_to_pdf  # noqa: E402

SIZE_TITLE = 14
SIZE_SECTION = 11
SIZE_BODY = 10.5
SIZE_FOOT = 9
RGB_MUTED = (80, 110, 140)

SPECS = [
    {
        "id": "A",
        "dir": ROOT / "printables" / "midterm" / "A-期中综合练习卷",
        "stem": "期中综合练习卷",
        "title": "数学 · 四上 · 期中综合练习卷",
        "subtitle": "原卷：2026 学年质量检测卷（期中）· 90 分钟 · 100 分",
        "total_pages": 4,  # page 5 missing
        "note": "原卷共 5 页，第 5 页照片缺失；本册为第 1–4 页清晰重排。",
    },
    {
        "id": "D",
        "dir": ROOT / "printables" / "midterm" / "D-期中重点练计算和附加卷",
        "stem": "期中重点练计算和附加卷",
        "title": "数学 · 四上 · 期中重点练计算和附加卷",
        "subtitle": "原卷：2026 人教版四上期中测试卷 · 90 分钟 · 100+10 分",
        "total_pages": 4,
        "note": "侧重计算、组数、动手操作与附加题；含附加题 10 分。",
    },
]


def set_run_font(run, name="宋体", size=SIZE_BODY, bold=False, color=None):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def add_para(doc, text, *, size=SIZE_BODY, bold=False, align=None, space_after=3, space_before=0, color=None, font="宋体"):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.25
    run = p.add_run(text)
    set_run_font(run, name=font, size=size, bold=bold, color=color)
    return p


def new_doc() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = Cm(1.6)
    sec.right_margin = Cm(1.6)
    sec.top_margin = Cm(1.2)
    sec.bottom_margin = Cm(1.2)
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(SIZE_BODY)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return doc


def clean_line(s: str) -> str:
    s = s.strip()
    s = s.replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
    s = s.replace("\\times", "×").replace("\\circ", "°").replace("\\star", "☆").replace("\\diamond", "◇")
    s = s.replace("\\triangle", "△").replace("\\angle", "∠").replace("\\square", "□")
    s = re.sub(r"\\\w+", "", s)
    s = s.replace("**", "").replace("*", "")
    s = re.sub(r"^#+\s*", "", s)
    return s.strip()


def split_pages(md: str) -> list[str]:
    parts = re.split(r"\n## 第\s*\d+\s*页[^\n]*\n", md)
    # parts[0] is preamble; rest are pages
    pages = [p.strip() for p in parts[1:] if p.strip()]
    # drop missing-page stubs
    out = []
    for p in pages:
        if "缺失" in p[:40] and len(p) < 80:
            continue
        out.append(p)
    return out


def write_page(doc: Document, body: str, *, title: str, subtitle: str, page: int, total: int, first: bool, note: str = ""):
    if first:
        add_para(doc, title, size=SIZE_TITLE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, font="黑体")
        add_para(doc, subtitle, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, color=RGB_MUTED)
        add_para(doc, "学校____________　四年级____班　姓名____________", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
        if note:
            add_para(doc, note, size=9, space_after=6, color=RGB_MUTED)

    skip_table = False
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("|"):
            # compact table row into one line
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            add_para(doc, "　".join(cells), size=10, space_after=2)
            continue
        if line.startswith("---"):
            continue
        text = clean_line(line)
        if not text:
            continue
        if text.startswith("### "):
            add_para(doc, text[4:], size=SIZE_SECTION, bold=True, space_before=6, space_after=3, font="黑体")
        elif text.startswith("【图"):
            add_para(doc, text, size=9.5, space_after=4, color=RGB_MUTED)
        elif re.match(r"^\d+[\.、]", text) or text.startswith("（"):
            add_para(doc, text, size=SIZE_BODY, space_after=4)
        else:
            add_para(doc, text, size=SIZE_BODY, space_after=3)

    add_para(
        doc,
        f"数学 · 四上 · 期中练习　第 {page} 页（共 {total} 页）",
        size=SIZE_FOOT,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=8,
        space_after=0,
        color=RGB_MUTED,
    )


def build_one(spec: dict, word) -> Path:
    md_path = spec["dir"] / "TRANSCRIPT.md"
    md = md_path.read_text(encoding="utf-8")
    pages = split_pages(md)
    if not pages:
        raise SystemExit(f"no pages in {md_path}")

    tmp = ROOT / "_tmp" / f"midterm_{spec['id']}_{time.strftime('%H%M%S')}"
    tmp.mkdir(parents=True, exist_ok=True)
    page_pdfs = []
    total = min(len(pages), spec["total_pages"])

    for i, body in enumerate(pages[:total], 1):
        doc = new_doc()
        write_page(
            doc,
            body,
            title=spec["title"],
            subtitle=spec["subtitle"],
            page=i,
            total=total,
            first=(i == 1),
            note=spec.get("note", "") if i == 1 else "",
        )
        docx_path = tmp / f"p{i}.docx"
        pdf_path = tmp / f"p{i}.pdf"
        doc.save(str(docx_path))
        docx_to_pdf(docx_path, pdf_path, word)
        n = pymupdf.open(pdf_path).page_count
        pymupdf.open(pdf_path).close()
        if n > 1:
            # shrink spacing isn't available post-hoc; warn and keep first page only via fit warning
            print(f"WARN {spec['id']} p{i} spilled to {n} pages — content dense")
        page_pdfs.append(pdf_path)
        print(spec["id"], f"p{i}", "word_pages", n)

    # merge docx
    stem = spec["dir"] / spec["stem"]
    first = word.Documents.Open(str((tmp / "p1.docx").resolve()))
    for i in range(2, len(page_pdfs) + 1):
        end = first.Content
        end.Collapse(0)
        end.InsertBreak(7)
        end = first.Content
        end.Collapse(0)
        end.InsertFile(str((tmp / f"p{i}.docx").resolve()))
    first.SaveAs(str(Path(str(stem) + ".docx").resolve()))
    first.Close(False)

    q_out = Path(str(stem) + "_试卷.pdf")
    full = pymupdf.open()
    for p in page_pdfs:
        src = pymupdf.open(p)
        # if multi-page, take all pages (better than dropping)
        full.insert_pdf(src)
        src.close()
    full.save(q_out, deflate=True, garbage=4)
    full.close()

    # lightweight answer stub
    ans = new_doc()
    add_para(ans, spec["title"] + " · 参考答案", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font="黑体")
    add_para(ans, "答案页待按原卷补全；先交付清晰试卷。", size=10.5, space_after=8, color=RGB_MUTED)
    ans_docx = Path(str(stem) + "_答案.docx")
    ans_pdf = Path(str(stem) + "_答案.pdf")
    ans_tmp = tmp / "ans.docx"
    ans.save(str(ans_tmp))
    docx_to_pdf(ans_tmp, tmp / "ans.pdf", word)
    shutil.copy2(ans_tmp, ans_docx)
    shutil.copy2(tmp / "ans.pdf", ans_pdf)

    combo = Path(str(stem) + ".pdf")
    c = pymupdf.open()
    q = pymupdf.open(q_out)
    c.insert_pdf(q)
    q.close()
    a = pymupdf.open(ans_pdf)
    c.insert_pdf(a)
    a.close()
    c.save(combo, deflate=True, garbage=4)
    c.close()

    print("OK", q_out, "pages", pymupdf.open(q_out).page_count)
    return q_out


def main() -> int:
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for spec in SPECS:
            build_one(spec, word)
    finally:
        word.Quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
