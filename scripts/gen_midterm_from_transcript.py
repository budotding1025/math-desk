# -*- coding: utf-8 -*-
"""Build midterm A/D clear Word+PDF from TRANSCRIPT.md (exam-from-photo).

作答留白优先：加宽填空/下划线，竖式与应用题加作答行；
每源页导出后若超一页，再逐步收紧留白，保证整卷仍为 4 页。
"""
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

# 宽填空：括号内下划线，方便手写；竖式与应用题另加行
BLANK = "（________）"
BLANK_DEG = "（________）°"
LINE = "________________________________"
LINE_WIDE = "________________________________________________"

SPECS = [
    {
        "id": "A",
        "dir": ROOT / "printables" / "midterm" / "A-期中综合练习卷",
        "stem": "期中综合练习卷",
        "title": "数学 · 四上 · 期中综合练习卷",
        "subtitle": "原卷：2026 学年质量检测卷（期中）· 90 分钟 · 100 分",
        "total_pages": 4,
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


def add_para(
    doc,
    text,
    *,
    size=SIZE_BODY,
    bold=False,
    align=None,
    space_after=3,
    space_before=0,
    color=None,
    font="宋体",
    line_spacing=1.28,
):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line_spacing
    run = p.add_run(text)
    set_run_font(run, name=font, size=size, bold=bold, color=color)
    return p


def gap(doc, pt: float):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(pt)
    pf.line_spacing = 1.0
    run = p.add_run("")
    set_run_font(run, size=1)
    return p


def write_lines(doc, n: int, *, width: str = LINE, space_after: float = 8):
    for _ in range(max(0, n)):
        add_para(doc, "　　" + width, size=SIZE_BODY, space_after=space_after, line_spacing=1.35)


def new_doc() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = Cm(1.5)
    sec.right_margin = Cm(1.5)
    sec.top_margin = Cm(1.1)
    sec.bottom_margin = Cm(1.1)
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


def widen_blanks(text: str) -> str:
    """加宽填空与算式等号后的作答位。"""
    text = re.sub(r"（\s*）°", BLANK_DEG, text)
    text = re.sub(r"（　+）°", BLANK_DEG, text)
    text = re.sub(r"（\s*）", BLANK, text)
    text = re.sub(r"（　+）", BLANK, text)
    # 125×8= / 末尾 = → 加作答下划线（已有则跳过）
    text = re.sub(r"=(?!______)(?=\s|$|　)", "= ______", text)
    return text


def split_pages(md: str) -> list[str]:
    parts = re.split(r"\n## 第\s*\d+\s*页[^\n]*\n", md)
    pages = [p.strip() for p in parts[1:] if p.strip()]
    out = []
    for p in pages:
        if "缺失" in p[:40] and len(p) < 80:
            continue
        out.append(p)
    return out


def is_section(text: str) -> bool:
    return bool(re.match(r"^[一二三四五六七八九十]+[、.．]", text)) or text.startswith("附加")


def is_item(text: str) -> bool:
    return bool(re.match(r"^(\d+[\.、．]|（\d+）|\(\d+\))", text))


def section_kind(title: str) -> str:
    t = title
    if any(k in t for k in ("解决问题", "应用")):
        return "word"
    if any(k in t for k in ("计算", "口算", "竖式")):
        return "calc"
    if any(k in t for k in ("动手", "按要求", "操作")):
        return "draw"
    if any(k in t for k in ("填空",)):
        return "blank"
    if any(k in t for k in ("选择",)):
        return "choice"
    if any(k in t for k in ("判断",)):
        return "choice"  # 括号已加宽，不再额外竖空
    if any(k in t for k in ("附加", "组成", "组数")):
        return "blank"
    return "other"


class Layout:
    """可调留白档位：level 越大越松。"""

    def __init__(self, level: int = 3):
        self.level = max(0, min(5, level))

    @property
    def q_after(self) -> float:
        return [3, 4, 5, 6, 8, 10][self.level]

    @property
    def section_before(self) -> float:
        return [3, 4, 5, 6, 7, 8][self.level]

    @property
    def blank_gap(self) -> float:
        # 填空题后竖向作答/草稿空
        return [4, 8, 12, 16, 20, 24][self.level]

    @property
    def word_lines(self) -> int:
        return [1, 2, 2, 3, 3, 4][self.level]

    @property
    def word_line_after(self) -> float:
        return [5, 6, 7, 8, 9, 10][self.level]

    @property
    def calc_gap(self) -> float:
        # 竖式区整块高度
        return [18, 28, 36, 44, 52, 60][self.level]

    @property
    def draw_gap(self) -> float:
        return [28, 40, 52, 64, 76, 88][self.level]

    @property
    def line_spacing(self) -> float:
        return [1.15, 1.2, 1.25, 1.28, 1.3, 1.32][self.level]


def write_page(
    doc: Document,
    body: str,
    *,
    title: str,
    subtitle: str,
    page: int,
    total: int,
    first: bool,
    note: str = "",
    layout: Layout | None = None,
):
    L = layout or Layout(3)
    if first:
        add_para(
            doc,
            title,
            size=SIZE_TITLE,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_after=2,
            font="黑体",
            line_spacing=L.line_spacing,
        )
        add_para(
            doc,
            subtitle,
            size=9.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_after=2,
            color=RGB_MUTED,
            line_spacing=L.line_spacing,
        )
        add_para(
            doc,
            "学校____________　四年级____班　姓名____________",
            size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_after=4,
            line_spacing=L.line_spacing,
        )
        if note:
            add_para(
                doc,
                note,
                size=9,
                space_after=4,
                color=RGB_MUTED,
                line_spacing=L.line_spacing,
            )

    kind = "other"
    pending_after: str | None = None  # blank | word | calc_row | draw

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            add_para(
                doc,
                "　".join(cells),
                size=10,
                space_after=2,
                line_spacing=L.line_spacing,
            )
            continue
        if line.startswith("---"):
            continue

        text = clean_line(line)
        if not text:
            continue

        # flush previous item's answer space before next major item/section
        def flush():
            nonlocal pending_after
            if pending_after == "blank":
                gap(doc, L.blank_gap)
            elif pending_after == "word":
                write_lines(doc, L.word_lines, width=LINE_WIDE, space_after=L.word_line_after)
            elif pending_after == "calc_row":
                gap(doc, L.calc_gap)
            elif pending_after == "draw":
                gap(doc, L.draw_gap)
            pending_after = None

        if text.startswith("### ") or is_section(text.lstrip("#").strip()):
            flush()
            title_txt = text[4:] if text.startswith("### ") else text
            kind = section_kind(title_txt)
            add_para(
                doc,
                title_txt,
                size=SIZE_SECTION,
                bold=True,
                space_before=L.section_before,
                space_after=3,
                font="黑体",
                line_spacing=L.line_spacing,
            )
            continue

        if text.startswith("【图"):
            # 长图注吃版面；收紧时改短占位，把竖直空间留给作答
            if L.level <= 2 and len(text) > 36:
                text = "【图：见题意示意，可在空白处作图】"
            add_para(doc, text, size=9, space_after=2, color=RGB_MUTED, line_spacing=1.1)
            if kind == "draw":
                pending_after = "draw"
            continue

        text = widen_blanks(text)

        if is_item(text):
            flush()
            add_para(
                doc,
                text,
                size=SIZE_BODY,
                space_after=L.q_after,
                line_spacing=L.line_spacing,
            )
            if kind == "word":
                pending_after = "word"
            elif kind == "draw":
                pending_after = "draw"
            elif kind == "blank":
                pending_after = "blank"
            elif kind == "calc":
                if "列竖式" in text or "验算" in text:
                    pending_after = "calc_row"
                else:
                    pending_after = "blank"
            elif kind == "choice":
                pending_after = None
            else:
                if re.search(r"[？?]", text) and ("分" in text or text.rstrip().endswith(("？", "?"))):
                    pending_after = "word"
                elif "画" in text and "角" in text:
                    pending_after = "draw"
                else:
                    pending_after = "blank"
            continue

        # 续行：口算/竖式算式行、选项等
        add_para(doc, text, size=SIZE_BODY, space_after=max(2, L.q_after - 2), line_spacing=L.line_spacing)
        if kind == "calc" and ("×" in text or "≈" in text) and ("=" in text or "≈" in text):
            if text.count("=") + text.count("≈") >= 2:
                # 多道口算：行末略空
                pending_after = "blank"
            else:
                # 竖式算式行
                pending_after = "calc_row"
        elif kind == "word" and ("？" in text or "?" in text):
            pending_after = "word"
        elif kind == "choice":
            pending_after = None

    # end of page
    if pending_after == "blank":
        gap(doc, L.blank_gap)
    elif pending_after == "word":
        write_lines(doc, L.word_lines, width=LINE_WIDE, space_after=L.word_line_after)
    elif pending_after == "calc_row":
        gap(doc, L.calc_gap)
    elif pending_after == "draw":
        gap(doc, L.draw_gap)

    add_para(
        doc,
        f"数学 · 四上 · 期中练习　第 {page} 页（共 {total} 页）",
        size=SIZE_FOOT,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=6,
        space_after=0,
        color=RGB_MUTED,
        line_spacing=1.15,
    )


def export_fitted_page(
    word,
    body: str,
    *,
    spec: dict,
    page: int,
    total: int,
    tmp: Path,
    first: bool,
) -> Path:
    """从宽松到收紧试排，尽量撑满一页且不溢出。"""
    # 先试最松，溢出则降档
    chosen_level = 0
    pdf_path = tmp / f"p{page}.pdf"
    docx_path = tmp / f"p{page}.docx"

    for level in range(5, -1, -1):
        doc = new_doc()
        write_page(
            doc,
            body,
            title=spec["title"],
            subtitle=spec["subtitle"],
            page=page,
            total=total,
            first=first,
            note=spec.get("note", "") if first else "",
            layout=Layout(level),
        )
        trial_docx = tmp / f"p{page}_L{level}.docx"
        trial_pdf = tmp / f"p{page}_L{level}.pdf"
        doc.save(str(trial_docx))
        docx_to_pdf(trial_docx, trial_pdf, word)
        n = pymupdf.open(trial_pdf).page_count
        pymupdf.open(trial_pdf).close()
        print(spec["id"], f"p{page}", f"L{level}", "word_pages", n)
        if n <= 1:
            chosen_level = level
            shutil.copy2(trial_docx, docx_path)
            shutil.copy2(trial_pdf, pdf_path)
            break
        # 最紧仍溢出：仍采用，并只取首页（极少见）
        if level == 0:
            chosen_level = 0
            shutil.copy2(trial_docx, docx_path)
            src = pymupdf.open(trial_pdf)
            out = pymupdf.open()
            out.insert_pdf(src, from_page=0, to_page=0)
            src.close()
            out.save(pdf_path)
            out.close()
            print(f"WARN {spec['id']} p{page} still spilled at L0 — clipped to 1 page")
    else:
        pass

    print(spec["id"], f"p{page}", "use", f"L{chosen_level}")
    return pdf_path


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
        pdf_path = export_fitted_page(
            word,
            body,
            spec=spec,
            page=i,
            total=total,
            tmp=tmp,
            first=(i == 1),
        )
        page_pdfs.append(pdf_path)

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
        full.insert_pdf(src)
        src.close()
    full.save(q_out, deflate=True, garbage=4)
    full.close()

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

    n_pages = pymupdf.open(q_out).page_count
    pymupdf.open(q_out).close()
    print("OK", q_out, "pages", n_pages)
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
