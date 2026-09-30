# -*- coding: utf-8 -*-
"""
统一考前卷形式：4 页试卷 + 可单打答案页（另有合订本=试卷+答案）。

- 已有 JPG 拆页：不足 4 页时补「待补」空白页
- 尚无源卷（U6–U9）：生成 4 页练习框架 + 答案框架
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
CN = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]

FOCUS = {
    "u01": ("大数的认识", ["读数写数", "改写省略与近似", "数位意义", "情境大数"], "见 answers/U1_*.md"),
    "u02": ("角的度量", ["角的分类与度数", "量角易错与拼角", "画角", "生活中的角"], "见 answers/U2_*.md"),
    "u03": ("三位数乘两位数", ["口算与竖式", "部分积意义", "估算够用", "乘应用题"], "见 answers/U3-U5_*.md · 三位数乘"),
    "u04": ("数量关系", ["总价单价数量", "路程速度时间", "问哪个量", "单位统一比较"], "见 answers/U3-U5_*.md · 数量关系"),
    "u05": ("平行四边形和梯形", ["平行与垂直", "梯形/平行四边形", "周长", "作图"], "见 answers/U3-U5_*.md · 平行四边形"),
    "u06": ("除数是两位数的除法", ["口算竖式", "试商", "商的变化", "除法应用"], "待按原卷补全答案"),
    "u07": ("条形统计图", ["读图", "复式条形图", "制图", "提出问题"], "待按原卷补全答案"),
    "u08": ("数学广角——优化", ["并行安排", "烙饼", "对策", "生活优化"], "待按原卷补全答案"),
    "u09": ("总复习", ["数与代数", "图形几何", "统计", "广角综合"], "待按原卷补全答案"),
}

STEM = {
    "u01": "U1_四上_第一单元_大数的认识",
    "u02": "U2_四上_第二单元_角的度量",
    "u03": "U3_四上_第三单元_三位数乘两位数",
    "u04": "U4_四上_第四单元_数量关系",
    "u05": "U5_四上_第五单元_平行四边形和梯形",
    "u06": "U6_四上_第六单元_除数是两位数的除法",
    "u07": "U7_四上_第七单元_条形统计图",
    "u08": "U8_四上_第八单元_数学广角——优化",
    "u09": "U9_四上_第九单元_总复习",
}


def exam_dir(uid: str) -> Path:
    return ROOT / "printables" / uid / "04-考前测试"


def title_of(uid: str) -> str:
    no = int(uid[1:])
    return f"第{CN[no-1]}单元 · {FOCUS[uid][0]}"


def draw_header(page, title: str, sub: str):
    html = (
        "<div style='font-family:sans-serif'>"
        "<div style='font-size:11pt;color:#1e7eb8;font-weight:700'>数学书桌 · Math Desk</div>"
        f"<div style='font-size:16pt;margin-top:6px;font-weight:700'>{title}</div>"
        f"<div style='font-size:10pt;color:#666;margin-top:4px'>{sub}</div>"
        "</div>"
    )
    page.insert_htmlbox(pymupdf.Rect(36, 28, 559, 95), html)
    page.draw_line(pymupdf.Point(36, 100), pymupdf.Point(559, 100), color=(0.75, 0.85, 0.92), width=1)


def placeholder_page_into(doc: pymupdf.Document, title: str, page_no: int, reason: str):
    page = doc.new_page(width=595, height=842)
    draw_header(page, title, f"试卷第 {page_no} / 4 页　|　{reason}")
    body = (
        "<div style='font-family:sans-serif;font-size:12pt;line-height:1.6'>"
        "<p>学校____________　四年级____班　姓名____________</p>"
        "<p style='color:#c0392b;font-size:14pt'><b>【待补】</b>本页源扫描尚未上传。</p>"
        "<p style='color:#666'>上传第 3–4 页 JPG 后可再生成完整卷。</p>"
        "<p>1. ________________________________</p>"
        "<p>2. ________________________________</p>"
        "<p>3. ________________________________</p>"
        "<p>4. ________________________________</p>"
        "<p>5. ________________________________</p>"
        "<p>6. ________________________________</p>"
        "</div>"
    )
    page.insert_htmlbox(pymupdf.Rect(36, 110, 559, 800), body)


def framework_question_pages(uid: str) -> pymupdf.Document:
    name, topics, _ = FOCUS[uid]
    title = title_of(uid)
    doc = pymupdf.open()
    for i, topic in enumerate(topics, 1):
        page = doc.new_page(width=595, height=842)
        draw_header(page, title, f"试卷第 {i} / 4 页　|　围绕：{topic}　|　30–40 分钟")
        body = (
            "<div style='font-family:sans-serif;font-size:12pt;line-height:1.7'>"
            "<p>学校____________　四年级____班　姓名____________</p>"
            f"<p style='color:#1e7eb8'><b>本页主题：{topic}</b></p>"
            "<p style='font-size:10pt;color:#666'>【说明】原卷 JPG 待上传；以下为练习框架，可先练题型。</p>"
            "<p>1. ________________________________</p>"
            "<p>2. ________________________________</p>"
            "<p>3. ________________________________</p>"
            "<div style='border:1px solid #ccd;height:70px;margin:8px 0;padding:8px;color:#999'>（作图 / 竖式区）</div>"
            "<p>4. ________________________________</p>"
            "<p>5. ________________________________</p>"
            "<div style='border:1px solid #ccd;height:70px;margin:8px 0;padding:8px;color:#999'>（作图 / 竖式区）</div>"
            "<p>6. ________________________________</p>"
            "</div>"
        )
        page.insert_htmlbox(pymupdf.Rect(36, 110, 559, 800), body)
    return doc


def framework_answer_page(uid: str) -> pymupdf.Document:
    name, topics, ans_note = FOCUS[uid]
    title = title_of(uid)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    draw_header(page, title + " · 参考答案", "单独答案页 · 可只打印这一页")
    items = "".join(
        f"<p><b>第 {i} 页（{topic}）</b><br/>1–6 题答案：待原卷确定后补全。／可先对照日常变式自批。</p>"
        for i, topic in enumerate(topics, 1)
    )
    body = (
        "<div style='font-family:sans-serif;font-size:11pt;line-height:1.6'>"
        f"<p>{ans_note}</p>"
        f"{items}"
        "<p>订正记录：________________________________</p>"
        "</div>"
    )
    page.insert_htmlbox(pymupdf.Rect(36, 110, 559, 800), body)
    return doc


def find_existing_questions_pdf(uid: str) -> Path | None:
    d = exam_dir(uid)
    # prefer *_试卷.pdf
    cands = sorted(d.glob("*_试卷.pdf"))
    if cands:
        return cands[0]
    # else a non-答案, non-docx pdf that isn't only stub name weird
    for p in sorted(d.glob("*.pdf")):
        if "_答案" in p.name:
            continue
        if p.name.endswith("_试卷.pdf"):
            return p
        # skip if there's both full and 试卷 - already handled
    # full combined without 试卷 suffix - extract first N pages later
    for p in sorted(d.glob("*.pdf")):
        if "_答案" in p.name:
            continue
        if "待补" in p.name:
            continue
        return p
    return None


def ensure_four_page_questions(uid: str) -> Path:
    """Return path to 4-page 试卷.pdf"""
    d = exam_dir(uid)
    d.mkdir(parents=True, exist_ok=True)
    stem = STEM[uid]
    out_q = d / f"{stem}_试卷.pdf"
    title = title_of(uid)

    src = None
    # Prefer existing *_试卷.pdf
    for p in d.glob("*_试卷.pdf"):
        src = p
        break
    if src is None:
        # try rebuild from full pdf (without answer page = last page if pages>4?)
        for p in d.glob("*.pdf"):
            if "_答案" in p.name or "待补" in p.name:
                continue
            if p.name.endswith("_试卷.pdf"):
                continue
            # combined full often has N+1 pages
            src = p
            break

    doc_out = pymupdf.open()
    if src and src.exists() and "待补" not in src.name:
        src_doc = pymupdf.open(src)
        # If this is a full combined file (questions+answer), drop last page when pages>=3
        # Heuristic: if name has no _试卷 and page count in (3,5] treat last as answer
        n = src_doc.page_count
        take = n
        if "_试卷" not in src.name and n >= 3:
            # drop last answer page if present
            take = n - 1 if n in (3, 5) or (n > 4 and n <= 6) else min(n, 4)
            if n == 4 and "_试卷" not in src.name:
                # could be 4 question pages already (U1/U2 full before split) or 2q+...
                # For U1 full rebuilt: 4q+1ans=5. For old clean exams different.
                take = 4 if n == 4 else take
            if n == 5:
                take = 4  # 4q + 1ans
            if n == 3:
                take = 2  # 2q + 1ans
        take = min(take, 4)
        for i in range(take):
            doc_out.insert_pdf(src_doc, from_page=i, to_page=i)
        src_doc.close()
        while doc_out.page_count < 4:
            placeholder_page_into(
                doc_out,
                title,
                doc_out.page_count + 1,
                "源卷缺页 · 待上传 JPG",
            )
    else:
        # framework 4 pages
        fw = framework_question_pages(uid)
        doc_out.insert_pdf(fw)
        fw.close()

    # ensure exactly 4
    while doc_out.page_count < 4:
        placeholder_page_into(doc_out, title, doc_out.page_count + 1, "源卷缺页 · 待上传 JPG")
    if doc_out.page_count > 4:
        # trim
        trim = pymupdf.open()
        trim.insert_pdf(doc_out, from_page=0, to_page=3)
        doc_out.close()
        doc_out = trim

    doc_out.save(out_q, deflate=True, garbage=4)
    doc_out.close()
    return out_q


def ensure_answer_pdf(uid: str) -> Path:
    d = exam_dir(uid)
    stem = STEM[uid]
    out_a = d / f"{stem}_答案.pdf"
    # keep existing good answer if present and reasonably sized
    existing = list(d.glob("*_答案.pdf"))
    if existing and existing[0].stat().st_size > 5000 and uid in ("u01", "u02", "u03", "u04", "u05"):
        if existing[0] != out_a:
            shutil.copy2(existing[0], out_a)
        return out_a
    ans = framework_answer_page(uid)
    # For u01-u05 try to reuse existing answer file content by copying pages
    for p in d.glob("*_答案.pdf"):
        if p.name == out_a.name:
            continue
        try:
            old = pymupdf.open(p)
            if old.page_count >= 1 and p.stat().st_size > 20000:
                ans.close()
                shutil.copy2(p, out_a)
                old.close()
                return out_a
            old.close()
        except Exception:
            pass
    ans.save(out_a, deflate=True, garbage=4)
    ans.close()
    return out_a


def make_full(uid: str, q: Path, a: Path) -> Path:
    d = exam_dir(uid)
    stem = STEM[uid]
    out = d / f"{stem}.pdf"
    doc = pymupdf.open()
    doc.insert_pdf(pymupdf.open(q))
    doc.insert_pdf(pymupdf.open(a))
    doc.save(out, deflate=True, garbage=4)
    doc.close()
    return out


def cleanup_misc(uid: str):
    d = exam_dir(uid)
    keep_suffixes = ("_试卷.pdf", "_答案.pdf")
    stem = STEM[uid]
    keep = {
        f"{stem}_试卷.pdf",
        f"{stem}_答案.pdf",
        f"{stem}.pdf",
    }
    # also keep old partial-named files briefly? remove clearly wrong leftovers
    for p in list(d.glob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".pdf", ".docx"):
            continue
        # remove 待补 docx/pdf once replaced
        if "待补" in p.name and p.name not in keep:
            p.unlink()
            print(" removed", p.name)
        # remove misfiled 角 under u03 etc if stem mismatch badly
        if uid == "u03" and "角的度量" in p.name:
            p.unlink()
            print(" removed", p.name)
        if uid == "u04" and "三位数乘两位数" in p.name and "数量关系" not in p.name:
            p.unlink()
            print(" removed", p.name)


def sync_original(uid: str, files: list[Path]):
    short = FOCUS[uid][0]
    folder = ROOT / "units" / f"{uid}-{short}"
    orig = folder / "04-考前测试" / "original"
    orig.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, orig / f.name)


def main():
    manifest = []
    for i in range(1, 10):
        uid = f"u{i:02d}"
        print("==", uid, FOCUS[uid][0])
        cleanup_misc(uid)
        q = ensure_four_page_questions(uid)
        a = ensure_answer_pdf(uid)
        full = make_full(uid, q, a)
        sync_original(uid, [q, a, full])
        # count real content pages before placeholders - report 4
        qdoc = pymupdf.open(q)
        pages = qdoc.page_count
        qdoc.close()
        complete = uid in ("u01", "u02")  # only these have full uploaded 4 pages
        # u03-u05 partial but now padded to 4
        row = {
            "id": uid,
            "no": i,
            "name": title_of(uid),
            "short": FOCUS[uid][0],
            "examPdf": f"printables/{uid}/04-考前测试/{STEM[uid]}_试卷.pdf",
            "examFullPdf": f"printables/{uid}/04-考前测试/{STEM[uid]}.pdf",
            "examAnswerPdf": f"printables/{uid}/04-考前测试/{STEM[uid]}_答案.pdf",
            "examComplete": complete,
            "examPages": 4,
            "wrongPdf": f"printables/{uid}/05-错题库/{uid}-错题重练-模板.pdf",
        }
        manifest.append(row)
        print(" ", q.name, a.name, full.name, "pages", pages)

    # write data.js
    data_js = ROOT / "data.js"
    units_js = json.dumps(manifest, ensure_ascii=False, indent=2)
    # indent units array content
    body = f"""window.MATH_DESK_DATA = {{
  book: "四年级上册 · 人教版",
  brand: "数学书桌",
  currentUnitId: "u02",
  currentTrack: "daily",
  /**
   * 考前卷统一形式：4 页试卷（examPdf）+ 可单打答案页（examAnswerPdf）；
   * 合订本 examFullPdf = 试卷 + 答案。缺页处为「待补」占位，上传 JPG 后可再生成。
   */
  units: {units_js},
}};
"""
    data_js.write_text(body, encoding="utf-8")
    (ROOT / "scripts" / "_exam_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("updated data.js")


if __name__ == "__main__":
    main()
