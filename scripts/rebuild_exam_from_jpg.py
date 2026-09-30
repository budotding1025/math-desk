# -*- coding: utf-8 -*-
"""
考前卷严格对齐上传 JPG 排版：
  - 试卷页 = pages-hd 源页（放大锐化后铺满 A4，不重排文字）
  - 不足 4 页补「待补」
  - 答案页单独文字 PDF（可单打）；合订本 = 试卷 + 答案

文件名对齐 data.js（无 _部分 后缀）。
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pymupdf
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "_source" / "unit-tests" / "pages-hd"
ANSWERS = ROOT / "answers"
TMP = PAGES / "_pdf_jpg"
JPEG_Q = 92
A4_W, A4_H = 595, 842
MARGIN = 8  # 尽量贴边，接近原卷版心

CN = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]

UNITS = [
    {
        "id": "u01",
        "no": 1,
        "short": "大数的认识",
        "stem": "U1_四上_第一单元_大数的认识",
        "prefix": "u01",
        "answer_md": "U1_四上_第一单元_大数的认识-参考答案.md",
        "complete": True,
    },
    {
        "id": "u02",
        "no": 2,
        "short": "角的度量",
        "stem": "U2_四上_第二单元_角的度量",
        "prefix": "u02",
        "answer_md": "U2_四上_第二单元_角的度量-参考答案.md",
        "complete": True,
    },
    {
        "id": "u03",
        "no": 3,
        "short": "三位数乘两位数",
        "stem": "U3_四上_第三单元_三位数乘两位数",
        "prefix": "u03",
        "answer_md": "U3-U5_乘除法数量关系查漏.md",
        "complete": False,
    },
    {
        "id": "u04",
        "no": 4,
        "short": "数量关系",
        "stem": "U4_四上_第四单元_数量关系",
        "prefix": "u04",
        "answer_md": "U3-U5_乘除法数量关系查漏.md",
        "complete": False,
    },
    {
        "id": "u05",
        "no": 5,
        "short": "平行四边形和梯形",
        "stem": "U5_四上_第五单元_平行四边形和梯形",
        "prefix": "u05",
        "answer_md": "U3-U5_乘除法数量关系查漏.md",
        "complete": False,
    },
]


def find_pages(prefix: str) -> list[Path]:
    found = []
    for i in range(1, 9):
        png = PAGES / f"{prefix}-p{i:02d}.png"
        jpg = TMP / f"{prefix}-p{i:02d}.jpg"
        if png.exists():
            found.append(png)
        elif jpg.exists():
            found.append(jpg)
        else:
            break
    return found


def prepare_print_jpg(src: Path) -> Path:
    """2× 放大 + 轻度锐化/对比，减轻扫描发糊，但不改排版。"""
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"{src.stem}_print.jpg"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    # 目标约 1800–2200 宽，便于打印
    scale = 2.0 if w < 1400 else 1.5
    im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
    im.save(out, "JPEG", quality=JPEG_Q, optimize=True)
    return out


def insert_image_page(doc: pymupdf.Document, img_path: Path) -> None:
    jpg = prepare_print_jpg(img_path)
    page = doc.new_page(width=A4_W, height=A4_H)
    box = pymupdf.Rect(MARGIN, MARGIN, A4_W - MARGIN, A4_H - MARGIN)
    # 等比铺满版心（与 JPG 同构图）
    page.insert_image(box, filename=str(jpg), keep_proportion=True)


def placeholder_page(doc: pymupdf.Document, title: str, page_no: int) -> None:
    page = doc.new_page(width=A4_W, height=A4_H)
    page.insert_text((36, 40), "数学书桌 · Math Desk", fontsize=11, color=(0.12, 0.49, 0.72))
    page.insert_text((36, 62), title, fontsize=14, color=(0.1, 0.1, 0.1))
    page.insert_text((36, 82), f"试卷第 {page_no} / 4 页　|　源卷此页 JPG 尚未上传", fontsize=10, color=(0.4, 0.4, 0.4))
    page.draw_line(pymupdf.Point(36, 96), pymupdf.Point(A4_W - 36, 96), color=(0.75, 0.85, 0.92), width=1)
    y = 120
    page.insert_text((36, y), "【待补】上传对应页 JPG 后可按原卷排版补全。", fontsize=12, color=(0.75, 0.2, 0.15))
    y += 28
    for i in range(1, 9):
        page.insert_text((36, y), f"{i}. ________________________________________________", fontsize=11)
        y += 28
    page.insert_text(
        (36, A4_H - 36),
        f"{title}　第 {page_no} 页（共 4 页）",
        fontsize=9,
        color=(0.12, 0.49, 0.72),
    )


def build_answer_pdf(path: Path, title: str, md_name: str) -> None:
    """优先保留已有清晰文字答案；否则从 markdown 生成。"""
    if path.exists() and path.stat().st_size > 8000:
        # 若是扫描大图答案则重做
        try:
            d = pymupdf.open(path)
            imgs = sum(len(p.get_images()) for p in d)
            chars = sum(len(p.get_text().strip()) for p in d)
            d.close()
            if chars > 200 and imgs <= 2:
                return
        except Exception:
            pass

    md = ANSWERS / md_name
    body = ""
    if md.exists():
        import re

        text = md.read_text(encoding="utf-8")
        text = re.sub(r"^#+\s*", "", text, flags=re.M)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"^>\s*", "", text, flags=re.M)
        body = text.strip()[:7000]
    else:
        body = "参考答案待按原卷补全。"

    doc = pymupdf.open()
    page = doc.new_page(width=A4_W, height=A4_H)
    page.insert_text((36, 36), "数学书桌 · Math Desk", fontsize=11, color=(0.12, 0.49, 0.72))
    page.insert_text((36, 56), f"{title} · 参考答案", fontsize=14)
    page.insert_text((36, 74), "单独答案页 · 可只打印这一页", fontsize=9, color=(0.4, 0.4, 0.4))
    page.draw_line(pymupdf.Point(36, 86), pymupdf.Point(A4_W - 36, 86), color=(0.75, 0.85, 0.92), width=1)
    safe = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    html = f"<div style='font-size:10pt;line-height:1.4;font-family:sans-serif'>{safe}</div>"
    try:
        page.insert_htmlbox(pymupdf.Rect(36, 96, A4_W - 36, A4_H - 36), html)
    except Exception:
        y = 100
        for line in body.splitlines():
            if y > A4_H - 40:
                break
            page.insert_text((36, y), line[:90], fontsize=9)
            y += 12
    doc.save(path, deflate=True, garbage=4)
    doc.close()


def build_unit(u: dict) -> None:
    pages = find_pages(u["prefix"])
    out = ROOT / "printables" / u["id"] / "04-考前测试"
    out.mkdir(parents=True, exist_ok=True)
    title = f"第{CN[u['no']-1]}单元 · {u['short']}"
    stem = u["stem"]
    q_path = out / f"{stem}_试卷.pdf"
    a_path = out / f"{stem}_答案.pdf"
    full_path = out / f"{stem}.pdf"

    print(f"== {u['id']} pages_src={len(pages)}")

    # 试卷：源页 + 补足 4 页
    docq = pymupdf.open()
    for p in pages:
        insert_image_page(docq, p)
    while docq.page_count < 4:
        placeholder_page(docq, title, docq.page_count + 1)
    if docq.page_count > 4:
        trim = pymupdf.open()
        trim.insert_pdf(docq, from_page=0, to_page=3)
        docq.close()
        docq = trim
    docq.save(q_path, deflate=True, garbage=4)
    nq = docq.page_count
    docq.close()

    build_answer_pdf(a_path, title, u["answer_md"])

    full = pymupdf.open()
    q = pymupdf.open(q_path)
    full.insert_pdf(q)
    q.close()
    a = pymupdf.open(a_path)
    full.insert_pdf(a)
    a.close()
    full.save(full_path, deflate=True, garbage=4)
    full.close()

    # units 备份
    uf = ROOT / "units" / f"{u['id']}-{u['short']}" / "04-考前测试"
    (uf / "original").mkdir(parents=True, exist_ok=True)
    (uf / "source").mkdir(parents=True, exist_ok=True)
    for f in (q_path, a_path, full_path):
        shutil.copy2(f, uf / "original" / f.name)
    for p in pages:
        shutil.copy2(p, uf / "source" / p.name)

    print(f"  ok {q_path.name} pages={nq} size={q_path.stat().st_size}")


def main() -> int:
    for u in UNITS:
        build_unit(u)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
