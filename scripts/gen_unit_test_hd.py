# -*- coding: utf-8 -*-
"""
将 unit-test 双页扫描图拆成单页 → 放大为高清 → 生成 PDF / Word。
版式卷头使用天蓝色主色（见 theme.py）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageEnhance, ImageFilter
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Inches

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_source" / "unit-tests"
PAGES = SRC / "pages-hd"
OUT = ROOT / "printables" / "unit-tests"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import BRAND_LINE, RGB_SKY_DEEP, RGB_SKY_DARK  # noqa: E402

# 源图 → 输出 stem；complete=True 表示四页齐全
UNITS = [
    {
        "id": "u01",
        "name": "第一单元·大数的认识",
        "stem": "U1_四上_第一单元_大数的认识",
        "files": ["U1-1.png", "U1-2.png"],
        "complete": True,
        "pages_label": "共4页",
    },
    {
        "id": "u02",
        "name": "第二单元·角的度量",
        "stem": "U2_四上_第二单元_角的度量",
        "files": ["U2-1.png", "U2-2.png"],
        "complete": True,
        "pages_label": "共4页",
    },
    {
        "id": "u03",
        "name": "第三单元·三位数乘两位数（仅首页）",
        "stem": "U3_四上_第三单元_三位数乘两位数_部分",
        "files": ["U3.png"],
        "complete": False,
        "pages_label": "仅第1–2页（缺第3–4页）",
    },
    {
        "id": "u04",
        "name": "第四单元·数量关系（仅首页）",
        "stem": "U4_四上_第四单元_数量关系_部分",
        "files": ["U4.png"],
        "complete": False,
        "pages_label": "仅第1–2页（缺第3–4页）",
    },
    {
        "id": "u05",
        "name": "第五单元·平行四边形和梯形（仅首页）",
        "stem": "U5_四上_第五单元_平行四边形和梯形_部分",
        "files": ["U5.png"],
        "complete": False,
        "pages_label": "仅第1–2页（缺第3–4页）",
    },
]

SCALE = 2  # 放大倍数（兼顾清晰与仓库体积）
JPEG_QUALITY = 88


def enhance(im: Image.Image) -> Image.Image:
    """轻度锐化与对比，避免发糊。"""
    im = im.convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    return im


def split_spread(path: Path) -> tuple[Image.Image, Image.Image]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    mid = w // 2
    # 中间装订缝略裁一点，减少黑缝
    gap = max(2, w // 200)
    left = im.crop((0, 0, mid - gap // 2, h))
    right = im.crop((mid + gap // 2, 0, w, h))
    return left, right


def to_hd(page: Image.Image) -> Image.Image:
    page = enhance(page)
    w, h = page.size
    hd = page.resize((w * SCALE, h * SCALE), Image.Resampling.LANCZOS)
    # 轻微去噪边缘
    hd = hd.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
    return hd


def pages_from_unit(unit: dict) -> list[Image.Image]:
    pages: list[Image.Image] = []
    for name in unit["files"]:
        left, right = split_spread(SRC / name)
        pages.append(to_hd(left))
        pages.append(to_hd(right))
    return pages


def save_page_pngs(unit: dict, pages: list[Image.Image]) -> list[Path]:
    PAGES.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, im in enumerate(pages, 1):
        p = PAGES / f"{unit['id']}-p{i:02d}.png"
        im.save(p, "PNG", optimize=True)
        paths.append(p)
    return paths


def write_pdf(unit: dict, page_paths: list[Path]) -> Path:
    """嵌入 JPEG 以控制体积（GitHub <50MB）。"""
    OUT.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT / f"{unit['stem']}.pdf"
    tmp_dir = PAGES / "_pdf_jpg"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    a4_w, a4_h = 595, 842
    margin = 18
    box = pymupdf.Rect(margin, margin, a4_w - margin, a4_h - margin)
    for p in page_paths:
        jpg = tmp_dir / (p.stem + ".jpg")
        Image.open(p).convert("RGB").save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True)
        page = doc.new_page(width=a4_w, height=a4_h)
        page.insert_image(box, filename=str(jpg), keep_proportion=True)
    doc.save(pdf_path, deflate=True, garbage=4)
    doc.close()
    return pdf_path


def set_run_font(run, name="宋体", size=11, bold=False, color=None):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def write_word(unit: dict, page_paths: list[Path]) -> Path:
    """Word：天蓝卷头 + 每页嵌入高清页图（与源图一致，便于核对）。"""
    OUT.mkdir(parents=True, exist_ok=True)
    docx_path = OUT / f"{unit['stem']}.docx"
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(1.2)
    sec.right_margin = Cm(1.2)
    sec.top_margin = Cm(1.0)
    sec.bottom_margin = Cm(1.0)

    # 封面说明页
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(BRAND_LINE)
    set_run_font(r, size=18, bold=True, color=RGB_SKY_DEEP)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"四上 · {unit['name']}")
    set_run_font(r, size=14, bold=True, color=RGB_SKY_DARK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    status = "完整卷（与源扫描页一致）" if unit["complete"] else "部分卷 · 仅有首页扫描"
    r = p.add_run(f"{status}　|　{unit['pages_label']}　|　主色：天蓝")
    set_run_font(r, size=10, color=RGB_SKY_DEEP)

    note = doc.add_paragraph()
    r = note.add_run(
        "说明：下列各页为源卷高清拆页（放大锐化），内容与 JPG/PNG 扫描一致；"
        "缺页待你补图后可再生成。答案见 answers/ 目录。"
    )
    set_run_font(r, size=9, color=RGB_SKY_DARK)

    for i, path in enumerate(page_paths, 1):
        doc.add_page_break()
        head = doc.add_paragraph()
        head.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = head.add_run(f"{BRAND_LINE}　·　{unit['name']}　·　第 {i} 页")
        set_run_font(r, size=10, bold=True, color=RGB_SKY_DEEP)
        # 页图宽度约 18.6cm
        doc.add_picture(str(path), width=Cm(18.6))

    doc.save(str(docx_path))
    return docx_path


def main() -> int:
    if not SRC.exists():
        print(f"Missing source: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    for unit in UNITS:
        print(f"== {unit['id']} {unit['name']}")
        pages = pages_from_unit(unit)
        paths = save_page_pngs(unit, pages)
        pdf = write_pdf(unit, paths)
        docx = write_word(unit, paths)
        print(f"  pages: {len(paths)}")
        print(f"  PDF : {pdf.name}")
        print(f"  DOCX: {docx.name}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
