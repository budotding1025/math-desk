# -*- coding: utf-8 -*-
"""Finish remaining units / rebuild with fresh Word instance per unit."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import pymupdf
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_exam_a4_word import (  # noqa: E402
    OUT_MAP,
    PAGE_BUILDERS,
    UNIT_DIRS,
    build_answer_doc,
    fit_one,
)

TMP = ROOT / "_tmp" / "a4_word_pages"
EXP = ROOT / "_tmp" / "word_export"
TMP.mkdir(parents=True, exist_ok=True)
EXP.mkdir(parents=True, exist_ok=True)


def safe_copy(src: Path, dst: Path) -> None:
    """Copy via ASCII temp; tolerate locked/Chinese-path OSError on Windows."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    mid = EXP / f"_copy_{src.name}"
    try:
        shutil.copy2(src, mid)
        shutil.copy2(mid, dst)
    except OSError as e:
        # retry once after brief pause
        time.sleep(0.8)
        try:
            shutil.copy2(src, mid)
            shutil.copy2(mid, dst)
        except OSError:
            print("  skip copy:", dst.name, e)


def to_pdf(docx: Path, pdf: Path, word) -> None:
    ascii_pdf = EXP / f"{docx.stem}.pdf"
    if ascii_pdf.exists():
        try:
            ascii_pdf.unlink()
        except OSError:
            pass
    doc = word.Documents.Open(FileName=str(docx.resolve()), ConfirmConversions=False, ReadOnly=True, AddToRecentFiles=False)
    time.sleep(0.3)
    doc.SaveAs2(FileName=str(ascii_pdf.resolve()), FileFormat=17)
    doc.Close(SaveChanges=False)
    time.sleep(0.2)
    safe_copy(ascii_pdf, pdf)


def build_uid(uid: str) -> None:
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        stem = OUT_MAP[uid]
        stem.parent.mkdir(parents=True, exist_ok=True)
        builders = PAGE_BUILDERS[uid]
        print("==", uid)
        page_pdfs = []
        for i, builder in enumerate(builders, 1):
            docx = TMP / f"{uid}_p{i}.docx"
            pdf = TMP / f"{uid}_p{i}.pdf"
            builder().save(str(docx))
            to_pdf(docx, pdf, word)
            d = pymupdf.open(pdf)
            n, chars = d.page_count, sum(len(p.get_text().strip()) for p in d)
            d.close()
            if n > 1:
                print(f"  WARN p{i} overflowed to {n} pages ({chars} chars) — shrink layout, skip raster fit")
            d = pymupdf.open(pdf)
            print(f"  p{i} pages={d.page_count} chars={sum(len(p.get_text().strip()) for p in d)}")
            d.close()
            page_pdfs.append(pdf)

        # full docx via page join (skip if COM flaky): copy p1 only as editable base + note
        # Prefer merging PDF first
        q_out = Path(str(stem) + "_试卷.pdf")
        full = pymupdf.open()
        for p in page_pdfs:
            src = pymupdf.open(p)
            # 只用首页；超页说明排版需再收，勿栅格化糊图
            full.insert_pdf(src, from_page=0, to_page=0)
            src.close()
        full.save(q_out, deflate=True, garbage=4)
        full.close()

        # editable base：经 ASCII 中转
        safe_copy(TMP / f"{uid}_p1.docx", Path(str(stem) + ".docx"))

        titles = {
            "u01": "第一单元 · 大数的认识",
            "u02": "第二单元 · 角的度量",
            "u03": "第三单元 · 三位数乘两位数",
            "u04": "第四单元 · 数量关系",
            "u05": "第五单元 · 平行四边形和梯形",
        }
        ans_docx = TMP / f"{uid}_ans.docx"
        ans_pdf = TMP / f"{uid}_ans.pdf"
        build_answer_doc(uid, titles[uid]).save(str(ans_docx))
        to_pdf(ans_docx, ans_pdf, word)
        safe_copy(ans_docx, Path(str(stem) + "_答案.docx"))
        safe_copy(ans_pdf, Path(str(stem) + "_答案.pdf"))

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

        try:
            orig = ROOT / "units" / UNIT_DIRS[uid] / "04-考前测试" / "original"
            orig.mkdir(parents=True, exist_ok=True)
            for suffix in (".docx", ".pdf", "_试卷.pdf", "_答案.pdf", "_答案.docx"):
                src = Path(str(stem) + suffix)
                if src.exists():
                    safe_copy(src, orig / src.name)
        except OSError as e:
            print("  skip units/original copy:", e)
        print("  ok", q_out.stat().st_size)
    finally:
        try:
            word.Quit()
        except Exception:
            pass
        time.sleep(1.5)


def main() -> int:
    only = [a for a in sys.argv[1:] if a in PAGE_BUILDERS]
    for uid in only or list(PAGE_BUILDERS):
        build_uid(uid)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
