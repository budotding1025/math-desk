# -*- coding: utf-8 -*-
"""
按 A4 原卷（照片糊，但版式可辨）用 Word 重排清晰卷：
  - 纸张 A4；边距 / 字号 / 图宽 / 题间距对齐原卷观感
  - 逐页生成再合并，页断与源卷 pages-hd 一致
  - 图用清晰重绘，不贴糊扫描
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pymupdf
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import RGB_SKY_DEEP  # noqa: E402  # 仅页脚淡色

DIAG = ROOT / "printables" / "_diagrams"

# A4 原卷观感参数（对照照片量边距；字号按小学单元卷常用五号/小四）
MARGIN_L = 1.5
MARGIN_R = 1.5
MARGIN_T = 1.1
MARGIN_B = 1.1
SIZE_TITLE = 15          # 卷头标题
SIZE_META = 10.5         # 时间、姓名栏
SIZE_BODY = 10.5         # 正文五号
SIZE_SECTION = 11        # 大题标题
SIZE_OPT = 10.5          # 选项
SIZE_FOOT = 9            # 页脚
SPACE_Q = 4              # 题间距（磅）—— 留作答空，但不松到半页空白
SPACE_LINE = 2
IMG_ABACUS = 7.0
IMG_NUMLINE = 12.0
IMG_PLACE = 10.0
IMG_MC = 13.5
IMG_SMALL = 6.5
IMG_MED = 9.0
IMG_WIDE = 12.5

OUT_MAP = {
    "u01": ROOT / "printables" / "u01" / "04-考前测试" / "U1_四上_第一单元_大数的认识",
    "u02": ROOT / "printables" / "u02" / "04-考前测试" / "U2_四上_第二单元_角的度量",
    "u03": ROOT / "printables" / "u03" / "04-考前测试" / "U3_四上_第三单元_三位数乘两位数",
    "u04": ROOT / "printables" / "u04" / "04-考前测试" / "U4_四上_第四单元_数量关系",
    "u05": ROOT / "printables" / "u05" / "04-考前测试" / "U5_四上_第五单元_平行四边形和梯形",
}
UNIT_DIRS = {
    "u01": "u01-大数的认识",
    "u02": "u02-角的度量",
    "u03": "u03-三位数乘两位数",
    "u04": "u04-数量关系",
    "u05": "u05-平行四边形和梯形",
}
ANSWER_MD = {
    "u01": ROOT / "answers" / "U1_四上_第一单元_大数的认识-参考答案.md",
    "u02": ROOT / "answers" / "U2_四上_第二单元_角的度量-参考答案.md",
    "u03": ROOT / "answers" / "U3-U5_乘除法数量关系查漏.md",
    "u04": ROOT / "answers" / "U3-U5_乘除法数量关系查漏.md",
    "u05": ROOT / "answers" / "U3-U5_乘除法数量关系查漏.md",
}


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
    space_after=SPACE_LINE,
    space_before=0,
    color=None,
    first_line=None,
):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.15
    if first_line is not None:
        pf.first_line_indent = first_line
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    return p


def add_image(doc, path: Path, width_cm: float):
    if not path.exists():
        add_para(doc, f"【缺图：{path.name}】", size=9, color=RGB_SKY_DEEP)
        return
    doc.add_picture(str(path), width=Cm(width_cm))
    p = doc.paragraphs[-1]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)


def new_doc() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = Cm(MARGIN_L)
    sec.right_margin = Cm(MARGIN_R)
    sec.top_margin = Cm(MARGIN_T)
    sec.bottom_margin = Cm(MARGIN_B)
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(SIZE_BODY)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return doc


def paper_header(doc, unit_cn: str, minutes="40"):
    add_para(
        doc,
        f"数学 · 四上 · {unit_cn}练习",
        size=SIZE_TITLE,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_para(doc, f"时间：{minutes} 分钟", size=SIZE_META, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    add_para(
        doc,
        "学校____________　四年级____班　姓名____________",
        size=SIZE_META,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )


def footer(doc, unit_cn: str, page: int, total: int = 4):
    add_para(
        doc,
        f"数学 · 四上 · {unit_cn}　第 {page} 页（共 {total} 页）",
        size=SIZE_FOOT,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=RGB_SKY_DEEP,
        space_before=6,
        space_after=0,
    )


def section(doc, title: str):
    add_para(doc, title, size=SIZE_SECTION, bold=True, space_before=6, space_after=4)


def q(doc, text, *, size=SIZE_BODY, space_after=SPACE_Q, first_line=None):
    add_para(doc, text, size=size, space_after=space_after, first_line=first_line)


def blank_page(unit_cn: str, page: int) -> Document:
    doc = new_doc()
    paper_header(doc, unit_cn)
    add_para(doc, "【待补】本页原卷照片尚未提供；上传后按原卷排版补全。", size=10, color=RGB_SKY_DEEP, space_after=10)
    for i in range(1, 8):
        q(doc, f"{i}. ________________________________________________", space_after=10)
    footer(doc, unit_cn, page)
    return doc


def docx_to_pdf(docx_path: Path, pdf_path: Path, word) -> None:
    docx_path = docx_path.resolve()
    pdf_path = pdf_path.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    # 先写到纯 ASCII 临时路径，避免中文路径导致 Word COM 异常
    ascii_pdf = ROOT / "_tmp" / "word_export" / f"{docx_path.stem}.pdf"
    ascii_pdf.parent.mkdir(parents=True, exist_ok=True)
    d = word.Documents.Open(str(docx_path), ReadOnly=True)
    try:
        d.ExportAsFixedFormat(str(ascii_pdf), 17)  # wdExportFormatPDF
    except Exception:
        d.SaveAs(str(ascii_pdf), FileFormat=17)
    d.Close(False)
    shutil.copy2(ascii_pdf, pdf_path)


def fit_one(pdf_path: Path) -> None:
    """若略超一页，等比缩进单页，避免丢题。"""
    doc = pymupdf.open(pdf_path)
    if doc.page_count <= 1:
        doc.close()
        return
    a4_w, a4_h = 595, 842
    margin = 20
    pixs = [doc[i].get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False) for i in range(doc.page_count)]
    doc.close()
    total_h = sum(p.height for p in pixs)
    max_w = max(p.width for p in pixs)
    avail_w, avail_h = a4_w - 2 * margin, a4_h - 2 * margin
    scale = min(avail_w / max_w, avail_h / total_h, 1.0)
    out = pymupdf.open()
    page = out.new_page(width=a4_w, height=a4_h)
    y = margin
    for pix in pixs:
        w, h = pix.width * scale, pix.height * scale
        x = margin + (avail_w - w) / 2
        page.insert_image(pymupdf.Rect(x, y, x + w, y + h), pixmap=pix)
        y += h
    out.save(pdf_path, deflate=True, garbage=4)
    out.close()


# ——— U1（对齐 u01-p01..p04） ———
def u01_p1() -> Document:
    doc = new_doc()
    paper_header(doc, "第一单元")
    section(doc, "一、填空。")
    q(doc, "1. 10 个一万是（　　），10 个一百万是（　　），一千万是（　　）个十万，一亿是（　　）个一百万。")
    q(doc, "2. 在 ○ 里填上“＞”“＜”或“＝”。", space_after=2)
    q(doc, "　　5430079 ○ 5430790　　　　1010100 ○ 110100", space_after=2)
    q(doc, "　　48 万 ○ 480000　　　　　　6299000 ○ 630 万")
    q(
        doc,
        "3. 马里亚纳海沟，是目前所知地球上最深的海沟，最深处在斐查兹海渊，为 11034 米，是地球的最深点。"
        "横线上的数读作（　　　　　　　　）米。它是由（　　）个万和（　　）个一组成的。",
    )
    q(
        doc,
        "4. 一个八位数，各个数位上都是 9，再加上 1，得到的数是（　　　　　　）。"
        "新得到的这个数是（　　）位数，最高位在（　　）位上。",
    )
    q(
        doc,
        "5. 嫦娥六号月球探测器从月球背面起飞，成功采回 1935.3 克样品。"
        "从月球到地球的平均距离约三十八万四千四百千米。"
        "横线上的数写作（　　　　）千米，省略“万”后面的尾数约是（　　）万千米。",
    )
    q(doc, "6. 28058306 这个数中，万级的数字 8 表示（　　　　　　），个级的数字 8 表示（　　　　　　）。")
    q(doc, "7. 下面 □ 里可以填哪些数字？把这些数字填在括号里。", space_after=2)
    q(doc, "　　8□989≈8 万，□里可以填（　　　　　　）。", space_after=2)
    q(doc, "　　10□0074000≈11 亿，□里可以填（　　　　　　）。")
    footer(doc, "第一单元", 1)
    return doc


def u01_p2() -> Document:
    doc = new_doc()
    q(
        doc,
        "8. 35□8270060 是一个十位数，□里填（　　）时，这个数最接近 35 亿；"
        "如果这个数最接近 36 亿，□里应填（　　）。",
    )
    q(
        doc,
        "9. 算盘是我国古代的伟大发明，是我国传统的计算工具。"
        "如图，算盘表示的数写作____________________。"
        "请在下面数线上用“↑”标出这个数的大致位置。",
        space_after=2,
    )
    add_image(doc, DIAG / "u1_abacus_numline_exact.jpg", IMG_NUMLINE)
    q(doc, "10. 11 颗珠子，放在不同的数位上表示的数不同。下图表示的是五位数 51023。", space_after=2)
    add_image(doc, DIAG / "u1_place_value_exact.jpg", IMG_PLACE)
    q(doc, "如果用这 11 颗珠子组成一个新的五位数（每个数位上都要有珠子），这个五位数最大是（　　　　）。")
    section(doc, "二、选一选。")
    q(doc, "1. 543100 中的“3”表示（　　）。", space_after=2)
    q(doc, "　　① 3 个一百　　② 3 个一千　　③ 3 个一万　　④ 3 个十万", size=SIZE_OPT)
    q(doc, "2. 有一个数，万级上是 406，个级上是 273，这个数是（　　）。", space_after=2)
    q(doc, "　　① 406273　　② 4060273　　③ 4062730　　④ 40600273", size=SIZE_OPT)
    q(doc, "3. 在数字 4 和 7 之间添（　　）个 0，可以组成四千万零七。", space_after=2)
    q(doc, "　　① 4　　② 5　　③ 6　　④ 7", size=SIZE_OPT)
    footer(doc, "第一单元", 2)
    return doc


def u01_p3() -> Document:
    doc = new_doc()
    q(doc, "4. 数学课上，四位同学用不同的方法表示了 120000，其中不正确的是（　　）。", space_after=2)
    add_image(doc, DIAG / "u1_mc120000_exact.jpg", IMG_MC)
    q(doc, "5. 一个数的近似数是 476 万，如果原来这个数万位上的数字是 6，那么原数千位上的数字最大是（　　）。", space_after=2)
    q(doc, "　　① 4　　② 5　　③ 0　　④ 9", size=SIZE_OPT)
    q(doc, "6. 下面四个数中，（　　）可能是图中 M 点表示的数。", space_after=2)
    add_image(doc, DIAG / "u1_numline_M_exact.jpg", IMG_MED)
    q(doc, "　　① 63000　　② 65000　　③ 67000　　④ 69000", size=SIZE_OPT)
    section(doc, "三、按要求完成下面各题。")
    q(doc, "1. 连一连。", space_after=2)
    q(doc, "　　一个 0 都不读　　　　读出一个 0　　　　读出两个 0", space_after=2)
    q(doc, "　　80072050　　80700025　　87025000　　87205000")
    q(doc, "2. 填上合适的数。", space_after=2)
    q(doc, "　　(1) 379614＝100000×（　）＋（　）×7＋（　）×9＋100×（　）＋10×（　）＋（　）×1", space_after=2)
    q(doc, "　　(2) 看数线填一填（50000—60000—70000）。")
    q(doc, "3. 将表格中四大行星到太阳的平均距离按从大到小的顺序排一排。", space_after=2)
    tb = doc.add_table(rows=2, cols=5)
    tb.style = "Table Grid"
    for i, h in enumerate(["行星", "地球", "木星", "水星", "金星"]):
        tb.rows[0].cells[i].text = h
    for i, d in enumerate(["到太阳的平均距离（千米）", "149600000", "778330000", "57910000", "108200000"]):
        tb.rows[1].cells[i].text = d
    q(doc, "从大到小：________________ → ________________ → ________________ → ________________")
    footer(doc, "第一单元", 3)
    return doc


def u01_p4() -> Document:
    doc = new_doc()
    section(doc, "四、列竖式计算（带※的题目要验算）。")
    q(doc, "1. 76×45＝　　　　　　　　　　2. 21.4－7.9＝", space_after=28)
    q(doc, "3. 572÷7＝　　　　　　　　　　※4. 843÷5＝", space_after=28)
    section(doc, "五、根据要求完成下面各题。")
    q(
        doc,
        "2022 年 2 月 4 日，第 24 届冬季奥林匹克运动会在北京开幕。"
        "国家体育场（鸟巢）于 2003 年 12 月 24 日开工建设，2008 年 6 月 28 日竣工，"
        "总投资 2267000000 元，建筑面积 258000 平方米，可容纳观众约 91000 人。"
        "本届冬奥会，中国体育代表团共获得 9 枚金牌、4 枚银牌、2 枚铜牌，共 15 枚奖牌。",
        size=10,
        first_line=Cm(0.74),
        space_after=6,
    )
    q(doc, "1. 将横线上的数按要求写下来。", space_after=2)
    q(doc, "　　2267000000 读作（　　　　　　　　　　　　　　）。", space_after=2)
    q(
        doc,
        "　　这个数中左边的“2”在（　　）位上，表示（　　　　　　）；"
        "右边的“2”在（　　）位上，表示（　　　　　　）。",
        space_after=2,
    )
    q(doc, "　　258000 省略万位后面的尾数，求出的近似数约是（　　）万。")
    q(doc, "2. 选一选。① 准确数　　② 近似数", space_after=2)
    q(doc, "　　“可容纳观众约 91000 人”中的 91000 是（　　）；“中国队共获得 9 枚金牌……”中的 9 是（　　）。")
    q(
        doc,
        "3. 冬奥会期间，小明看新闻时听到一条信息：“……带动约 3 亿人参与冰雪运动。”"
        "于是，他想利用所学的有关“四舍五入”的知识推测，这里的“约 3 亿人”最多可以是多少人。"
        "请把你的想法写出来。",
        space_after=2,
    )
    q(doc, "________________________________________________________________", space_after=2)
    q(doc, "________________________________________________________________")
    footer(doc, "第一单元", 4)
    return doc


# ——— U2 ———
def u02_p1() -> Document:
    doc = new_doc()
    paper_header(doc, "第二单元")
    section(doc, "一、填空。")
    q(doc, "1. 1 周角＝（　　）平角＝（　　）直角。", space_after=2)
    q(doc, "　　（　　）角＜（　　）角＜（　　）角＜（　　）角＜周角。")
    q(doc, "2. 从早上 6 时到中午 12 时，时针转过（　　）°，相当于 2 个（　　）角的度数。")
    q(doc, "3. 下图中箭头所指的位置表示（　　）角，请你用“△”标出周角的位置。", space_after=2)
    add_image(doc, DIAG / "u2_degree_ray_exact.jpg", IMG_WIDE)
    q(doc, "4. 东东在用量角器量角时，错误地把外圈刻度当成内圈刻度，读出的度数是 56°，正确的度数应该是（　　）°。")
    q(
        doc,
        "5. 如右图，城城用半圆形的材料制作了一个量角器，它被分成了 9 个同样大小的角。"
        "如果用这个量角器测量 ∠1 的大小，∠1＝（　　）°。",
        space_after=2,
    )
    add_image(doc, DIAG / "u2_9sector_exact.jpg", IMG_SMALL)
    q(
        doc,
        "6. “二十四节气”是古人通过观察天体运行，认知一年中时令、气候、物候等变化规律所形成的知识体系。"
        "古人将太阳周年运动轨迹 360° 划分为 24 等份，每一等份为一个节气，统称“二十四节气”，"
        "每个节气的太阳运动轨迹是（　　）°。",
        size=10,
    )
    section(doc, "二、选一选。")
    q(doc, "1. 两个锐角可以组成的角不可能是（　　）。", space_after=2)
    q(doc, "　　① 锐角　　② 直角　　③ 钝角　　④ 平角", size=SIZE_OPT)
    footer(doc, "第二单元", 1)
    return doc


def u02_p2() -> Document:
    doc = new_doc()
    q(doc, "2. 如图，汽车经过收费亭时，转杆会慢慢地升起。转杆升起的过程中，与竖杆形成的角的变化情况为（　　）。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_toll_exact.jpg", 8.0)
    q(doc, "　　① 直角→钝角→周角　　② 锐角→直角→钝角　　③ 直角→钝角→平角　　④ 锐角→钝角→直角", size=8.5, space_after=2)
    q(doc, "3. 从人体脊柱健康的角度考虑，座椅靠背角度在 103°～112° 之间。下面各图中符合要求的是（　　）。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_chairs_exact.jpg", 10.0)
    q(doc, "4. 丽丽将一张长方形纸进行折叠（如图），∠1 的度数是（　　）。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_fold_rect_exact.jpg", 4.8)
    q(doc, "　　① 90°　　② 105°　　③ 135°　　④ 150°", size=9.5, space_after=2)
    q(doc, "5. 思思选择了初级道，滑雪道和地面的夹角是 10°，爸爸选择了高级道，滑雪道和地面的夹角大约是（　　）。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_ski_exact.jpg", 7.0)
    q(doc, "　　① 20°　　② 40°　　③ 60°　　④ 80°", size=9.5, space_after=2)
    add_para(doc, "三、解决问题。", size=SIZE_SECTION, bold=True, space_before=2, space_after=2)
    q(doc, "1. 先估计，再量一量图中各角的度数并填空。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_measure_angles_exact.jpg", 8.2)
    q(doc, "　　∠1＝（　　）°　　　　∠2＝（　　）°", size=9.5, space_after=2)
    q(doc, "2. 选择合适的方法在方框中画出下面各角，并标明它们分别是哪一种角。", size=9.5, space_after=1)
    add_image(doc, DIAG / "u2_draw_boxes_exact.jpg", 9.5)
    q(doc, "　　(1) 50°（　　）角　　　　(2) 150°（　　）角", size=9.5)
    footer(doc, "第二单元", 2)
    return doc


def u02_p3() -> Document:
    doc = new_doc()
    q(doc, "3. 把一张圆形纸连续对折三次。想一想，填一填。", space_after=2)
    add_image(doc, DIAG / "u2_circle_fold_exact.jpg", IMG_WIDE)
    q(doc, "4. 想一想，填一填。", space_after=2)
    q(doc, "　　(1) 填出下面三角尺上每个角的度数。", space_after=2)
    add_image(doc, DIAG / "u2_set_squares_exact.jpg", 11.5)
    q(doc, "　　(2) 填出下面三角尺上所标角的度数。", space_after=2)
    add_image(doc, DIAG / "u2_compose_angles_exact.jpg", IMG_WIDE)
    q(doc, "5. 求出下面图中指定角的度数。", space_after=2)
    add_image(doc, DIAG / "u2_intersect_exact.jpg", IMG_WIDE)
    footer(doc, "第二单元", 3)
    return doc


def u02_p4() -> Document:
    doc = new_doc()
    q(doc, "6. 下面是一个破损的量角器，请你在这个破损的量角器上画一个 75° 的角，并在图中标出角的度数。", space_after=2)
    add_image(doc, DIAG / "u2_broken_protractor_exact.jpg", 9.5)
    q(
        doc,
        "7. 如下图，东东想折一个纸飞机，先把一张正方形纸对折产生一条折痕，再将点 B 和点 C 都折到折痕的点 G 上。"
        "已知 ∠1＝60°，那么 ∠2 等于多少度？",
        space_after=2,
    )
    add_image(doc, DIAG / "u2_plane_fold_exact.jpg", 11.5)
    q(doc, "8. 放风筝比赛时，选手们所用的风筝线一样长，假如他们都把风筝线放到最长。", space_after=2)
    add_image(doc, DIAG / "u2_kites_exact.jpg", 11.5)
    q(doc, "　　(1) 如图，量一量，甲的风筝线与地面的夹角是（　　）°，乙的风筝线与地面的夹角是（　　）°。", space_after=2)
    q(doc, "　　(2) 风筝飞的高度和风筝线与地面的夹角有什么关系？________________________________", space_after=2)
    q(doc, "　　(3) 如果丙的风筝线与地面的夹角为 30°，他的风筝飞得比甲、乙的高吗？请把这个角也在上图中画出来。")
    footer(doc, "第二单元", 4)
    return doc


# ——— U3 ———
def u03_p1() -> Document:
    doc = new_doc()
    paper_header(doc, "第三单元")
    section(doc, "一、填空。")
    q(doc, "1. 23 个 12 的和是（　　）。26 的 17 倍是（　　）。")
    q(doc, "2. 最大的两位数与最小的三位数的积是（　　）。")
    q(doc, "3. 457 加上（　　）正好是 82 的 9 倍。")
    q(
        doc,
        "4. 2024 年 10 月 30 日凌晨，我国神舟十九号载人飞船发射取得圆满成功，三名航天员顺利进驻中国空间站。"
        "中国空间站绕地球飞行一圈大约需要 90 分钟，照这样计算，一天（24 小时）可以绕地球飞行（　　）圈。",
    )
    q(doc, "5. 观察下面的算式和得数有什么特点，根据你的发现填一填。", space_after=2)
    q(doc, "　　12×9－8＝100", space_after=1)
    q(doc, "　　123×9－7＝1100", space_after=1)
    q(doc, "　　1234×9－6＝11100", space_after=1)
    q(doc, "　　12345×9－5＝（　　）", space_after=1)
    q(doc, "　　……", space_after=1)
    q(doc, "　　123456789×9－1＝（　　）")
    q(doc, "6. 在计算 12×14 这道题时，同学们用了不同的方法。在对的方法后面的（　　）内打“√”。", space_after=2)
    q(doc, "　　东东：14＋14＋14＋14＋14＋14＋14＋14＋14＋14＋14＋14（　　）", space_after=2)
    q(doc, "　　城城：12×7＋2（　　）", space_after=2)
    q(doc, "　　思思：14×6＋14×6（　　）", space_after=2)
    q(doc, "　　乐乐：12×10＋12×4（　　）")
    footer(doc, "第三单元", 1, 2)
    return doc


def u03_p2() -> Document:
    doc = new_doc()
    q(
        doc,
        "7. 一块长方形绿地，如果长增加 1 m，面积就增加 16 m²；"
        "如果宽增加 1 m，面积就增加 25 m²。这块绿地的面积是（　　）。",
    )
    section(doc, "二、选一选。")
    q(
        doc,
        "1. 我国发射的第一颗人造地球卫星绕地球 1 圈需要 114 分，绕地球 11 圈需要多少分？"
        "乐乐用如图所示的竖式进行了计算，竖式中“←”所指部分表示（　　）。",
        space_after=2,
    )
    add_image(doc, DIAG / "u3_114x11_exact.jpg", 5.5)
    q(doc, "　　① 人造地球卫星绕地球 1 圈需要 114 分", size=SIZE_OPT, space_after=1)
    q(doc, "　　② 人造地球卫星绕地球 1 圈需要 1140 分", size=SIZE_OPT, space_after=1)
    q(doc, "　　③ 人造地球卫星绕地球 10 圈需要 114 分", size=SIZE_OPT, space_after=1)
    q(doc, "　　④ 人造地球卫星绕地球 10 圈需要 1140 分", size=SIZE_OPT)
    q(
        doc,
        "2. 在用计算器计算 3090×120 时，错误地输成 3090×20。"
        "除了清除后再重新输入外，下列（　　）操作也可以得到正确结果。",
        space_after=2,
    )
    q(doc, "　　① ÷10　　② ×10　　③ ×6　　④ ÷6", size=SIZE_OPT)
    q(
        doc,
        "3. 学校开展“诗歌创作”活动，将优秀作品编辑成一本诗集。每本诗集需要 32 张纸，"
        "给四年级的 298 名同学每人制作一本诗集，需要准备多少张纸？"
        "下面四位同学，（　　）的估算方法能解决这个问题。",
        space_after=2,
    )
    q(doc, "　　① 东东：298×32≈8940（把 32 看作 30）", size=SIZE_OPT, space_after=1)
    q(doc, "　　② 城城：298×32≈8700（298≈290，32≈30）", size=SIZE_OPT, space_after=1)
    q(doc, "　　③ 思思：298×32≈9600（298≈300）", size=SIZE_OPT, space_after=1)
    q(doc, "　　④ 乐乐：298×32≈9000（298≈300，32≈30）", size=SIZE_OPT)
    footer(doc, "第三单元", 2, 2)
    return doc


# ——— U4 ———
def u04_p1() -> Document:
    doc = new_doc()
    paper_header(doc, "第四单元")
    section(doc, "一、填空。")
    q(
        doc,
        "1. 故宫文创店全天接待消费者 1280 人，上午 659 人，下午（　　）人。"
        "是根据数量关系（　　）－（　　）＝（　　）来解决问题的。",
    )
    q(
        doc,
        "2. 图书馆购买了 15 套《经典名著丛书》，每套 108 元，图书馆一共花了（　　）元，"
        "是根据数量关系（　　）×（　　）＝（　　）来解决问题的。",
    )
    q(
        doc,
        "3. 沪宁高速公路全长 274 千米，一辆汽车从南京开往上海，行驶 3 小时后离上海还有 34 千米，"
        "这辆汽车平均每小时行驶（　　）千米。",
    )
    q(doc, "4. 某校四年级男生 113 人，比女生少 46 人，四年级共有学生（　　）人。")
    q(doc, "5. 在括号里填“单价”“数量”“总价”或它们之间的关系式。", space_after=2)
    q(doc, "　　(1) 思思和妈妈购物时，妈妈说：“牛肉真是太贵了！”妈妈的说法指的是（　　）高。", space_after=2)
    q(doc, "　　(2) 每台笔记本电脑 4360 元，买 2 台要用多少钱？题目中已知（　　）和（　　），要求的是（　　）。", space_after=2)
    q(doc, "　　(3) 每套校服 120 元，买 5 套要用多少钱？解决这个问题用到的数量关系式是（　　）。")
    q(
        doc,
        "6. 王老师从 A 市到 B 市出差，两地相距约 1260 千米，她早上 8:50 出发，当天 14:50 到达。"
        "根据以上信息，可以推断她乘坐的交通工具是（　　）。",
        space_after=2,
    )
    tb = doc.add_table(rows=2, cols=5)
    tb.style = "Table Grid"
    for i, h in enumerate(["交通工具", "汽车", "普通列车", "高铁列车", "飞机"]):
        tb.rows[0].cells[i].text = h
    for i, h in enumerate(["速度", "80 千米/时", "120 千米/时", "230 千米/时", "730 千米/时"]):
        tb.rows[1].cells[i].text = h
    footer(doc, "第四单元", 1, 2)
    return doc


def u04_p2() -> Document:
    doc = new_doc()
    q(doc, "7. 竖式 125×23 中，箭头所指部分积表示（　　）件毛衣的总价，是（　　）元。", space_after=2)
    add_image(doc, DIAG / "u4_125x23_exact.jpg", 5.5)
    section(doc, "二、选一选。")
    q(doc, "1. 复兴号约 350 千米/时，15 分钟行驶多少千米？这个问题求的是（　　）。", space_after=2)
    q(doc, "　　① 速度　　② 路程　　③ 时间　　④ 车次", size=SIZE_OPT)
    q(doc, "2. 买 10 个篮球共 400 元，每个多少元？求的是（　　）。", space_after=2)
    q(doc, "　　① 单价　　② 数量　　③ 总价　　④ 速度", size=SIZE_OPT)
    q(doc, "3. 下面哪个速度最快？（先统一单位再比较）（　　）。", space_after=2)
    q(doc, "　　① 约 20 m/s　　② 约 5 km/min　　③ 约 900 km/h　　④ 约 90 km/h", size=SIZE_OPT)
    q(doc, "4. 骑行 225 米/分，骑 12 分钟。竖式 225×12 中箭头所指（方框内）一步表示（　　）。", space_after=2)
    add_image(doc, DIAG / "u4_225x12_exact.jpg", 5.5)
    q(doc, "　　① 1 分钟路程　　② 2 分钟路程　　③ 10 分钟路程　　④ 12 分钟路程", size=SIZE_OPT)
    q(doc, "5. 下列不能用 15×4 解决的是（　　）。", space_after=2)
    q(doc, "　　① 4 条丝带，每条 15 m，总长多少？", size=SIZE_OPT, space_after=1)
    q(doc, "　　② 甲有 15 元，乙是甲的 4 倍，乙有多少？", size=SIZE_OPT, space_after=1)
    q(doc, "　　③ 宽 15 m，长是宽的 4 倍，求面积。", size=SIZE_OPT, space_after=1)
    q(doc, "　　④ 鸡蛋原价 20 元/kg，现价 15 元/kg，买 4 kg 多少钱？", size=SIZE_OPT)
    footer(doc, "第四单元", 2, 2)
    return doc


# ——— U5 ———
def u05_p1() -> Document:
    doc = new_doc()
    paper_header(doc, "第五单元")
    section(doc, "一、填空。")
    q(doc, "1. 观察下面各图，量一量，并在括号里填上序号。", space_after=2)
    add_image(doc, DIAG / "u5_lines_exact.jpg", IMG_WIDE)
    q(doc, "　　互相垂直的是（　　），互相平行的是（　　）。")
    q(doc, "2. 在梯形下面的括号里画“○”，在平行四边形下面的括号里画“△”。", space_after=2)
    add_image(doc, DIAG / "u5_shapes_exact.jpg", IMG_WIDE)
    q(doc, "3. 从直线外一点到这条直线所画的（　　）最短，它的长度叫做这点到直线的（　　）。")
    q(
        doc,
        "4. 只有一组对边平行的四边形是（　　），互相平行的一组对边分别叫做（　　）和（　　），"
        "不平行的一组对边叫做（　　）。",
    )
    q(doc, "5. 一个梯形中最多有（　　）个直角，这样的梯形叫做（　　）梯形。")
    q(doc, "6. 等腰梯形的两腰（　　），两底角（　　）。")
    q(doc, "7. 一个平行四边形两条相邻的边长度分别是 15 厘米和 18 厘米，这个平行四边形的周长是（　　）厘米。")
    q(doc, "8. 有一组直线（如右图）：", space_after=2)
    add_image(doc, DIAG / "u5_abcd_exact.jpg", 8.0)
    q(doc, "　　其中直线（　　）和直线（　　）互相垂直；直线（　　）和直线（　　）互相平行。")
    footer(doc, "第五单元", 1, 2)
    return doc


def u05_p2() -> Document:
    doc = new_doc()
    section(doc, "二、选一选。")
    q(doc, "1. 被遮挡图形露出两边平行，它不可能是（　　）。", size=10, space_after=2)
    add_image(doc, DIAG / "u5_obscured_exact.jpg", 5.8)
    q(doc, "　　① 等腰梯形　　② 平行四边形　　③ 长方形　　④ 直角梯形", size=SIZE_OPT)
    q(doc, "2. 在等腰梯形中画一条直线，不能把它分成两个完全相同的（　　）。", size=10, space_after=2)
    q(doc, "　　① 梯形　　② 平行四边形　　③ 三角形　　④ 长方形", size=SIZE_OPT)
    q(doc, "3. 两组对边分别平行的四边形是（　　）。", size=10, space_after=2)
    q(doc, "　　① 直角梯形　　② 平行四边形　　③ 三角形　　④ 等腰梯形", size=SIZE_OPT)
    q(doc, "4. 用圆规比较线段 AB、CD 的长短（开口越大越长），结果是（　　）。", size=10, space_after=2)
    add_image(doc, DIAG / "u5_compass_exact.jpg", 8.0)
    q(doc, "　　① CD＞AB　　② CD＝AB　　③ CD＜AB　　④ 无法确定", size=SIZE_OPT)
    q(doc, "5. 如图，梯形 ABCD 中 AD∥BC，点 D 沿直线向 A 运动直至重合，图形变化顺序是（　　）。", size=10, space_after=2)
    add_image(doc, DIAG / "u5_trap_motion_exact.jpg", 7.2)
    q(doc, "　　① 梯形→平行四边形→梯形　　② 梯形→平行四边形→三角形", size=9, space_after=1)
    q(doc, "　　③ 梯形→三角形→平行四边形→梯形　　④ 梯形→平行四边形→梯形→三角形", size=9)
    section(doc, "三、解决问题。")
    q(doc, "1. （1）过角内一点 P，分别向两边作垂线。", size=10, space_after=2)
    add_image(doc, DIAG / "u5_angle_P_exact.jpg", 6.2)
    q(doc, "　　（2）过直线 l 上方点 A、下方点 B，分别作 l 的垂线。这两条垂线的位置关系是（　　）。", size=10, space_after=2)
    add_image(doc, DIAG / "u5_line_AB_exact.jpg", 7.5)
    footer(doc, "第五单元", 2, 2)
    return doc


PAGE_BUILDERS = {
    "u01": [u01_p1, u01_p2, u01_p3, u01_p4],
    "u02": [u02_p1, u02_p2, u02_p3, u02_p4],
    "u03": [u03_p1, u03_p2],
    "u04": [u04_p1, u04_p2],
    "u05": [u05_p1, u05_p2],
}


def build_answer_doc(uid: str, title: str) -> Document:
    doc = new_doc()
    add_para(doc, f"{title} · 参考答案", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    add_para(doc, "单独答案页 · 可只打印这一页", size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    md = ANSWER_MD.get(uid)
    if md and md.exists():
        for raw in md.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip()
            if not line or line.startswith(">"):
                continue
            if line.startswith("#"):
                add_para(doc, line.lstrip("# ").strip(), size=11, bold=True, space_before=4, space_after=2)
            else:
                add_para(doc, line.replace("**", "").replace("`", ""), size=9.5, space_after=1)
    else:
        add_para(doc, "参考答案待按原卷补全。", size=10, color=RGB_SKY_DEEP)
    return doc


def main() -> int:
    import win32com.client

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    tmp = ROOT / "_tmp" / "a4_word_pages"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        for uid, builders in PAGE_BUILDERS.items():
            stem = OUT_MAP[uid]
            stem.parent.mkdir(parents=True, exist_ok=True)
            print("==", uid)
            page_pdfs = []
            for i, builder in enumerate(builders, 1):
                docx_path = tmp / f"{uid}_p{i}.docx"
                pdf_path = tmp / f"{uid}_p{i}.pdf"
                builder().save(str(docx_path))
                docx_to_pdf(docx_path, pdf_path, word)
                before = pymupdf.open(pdf_path)
                n_before = before.page_count
                chars_before = sum(len(p.get_text().strip()) for p in before)
                before.close()
                if n_before > 1:
                    fit_one(pdf_path)
                after = pymupdf.open(pdf_path)
                print(
                    f"  p{i} word_pages={n_before} chars={chars_before} "
                    f"-> final_pages={after.page_count} final_chars={sum(len(p.get_text().strip()) for p in after)} "
                    f"size={pdf_path.stat().st_size}"
                )
                after.close()
                page_pdfs.append(pdf_path)

            # 合成为可编辑 docx（逐页粘贴）
            full_docx = Path(str(stem) + ".docx")
            first = word.Documents.Open(str((tmp / f"{uid}_p1.docx").resolve()))
            for i in range(2, len(builders) + 1):
                first.Paragraphs.Last.Range.InsertBreak(7)
                sub = word.Documents.Open(str((tmp / f"{uid}_p{i}.docx").resolve()))
                sub.Content.Copy()
                first.Paragraphs.Last.Range.Paste()
                sub.Close(False)
            first.SaveAs(str(full_docx.resolve()))
            first.Close(False)

            q_out = Path(str(stem) + "_试卷.pdf")
            full = pymupdf.open()
            for p in page_pdfs:
                src = pymupdf.open(p)
                full.insert_pdf(src, from_page=0, to_page=0)
                src.close()
            full.save(q_out, deflate=True, garbage=4)
            full.close()

            title_cn = {
                "u01": "第一单元 · 大数的认识",
                "u02": "第二单元 · 角的度量",
                "u03": "第三单元 · 三位数乘两位数",
                "u04": "第四单元 · 数量关系",
                "u05": "第五单元 · 平行四边形和梯形",
            }[uid]
            ans_docx = Path(str(stem) + "_答案.docx")
            ans_pdf = Path(str(stem) + "_答案.pdf")
            ans_tmp_docx = tmp / f"{uid}_答案.docx"
            ans_tmp_pdf = tmp / f"{uid}_答案.pdf"
            build_answer_doc(uid, title_cn).save(str(ans_tmp_docx))
            docx_to_pdf(ans_tmp_docx, ans_tmp_pdf, word)
            shutil.copy2(ans_tmp_docx, ans_docx)
            shutil.copy2(ans_tmp_pdf, ans_pdf)

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

            unit_name = UNIT_DIRS[uid]
            orig = ROOT / "units" / unit_name / "04-考前测试" / "original"
            orig.mkdir(parents=True, exist_ok=True)
            for suffix in (".docx", ".pdf", "_试卷.pdf", "_答案.pdf", "_答案.docx"):
                src = Path(str(stem) + suffix)
                if src.exists():
                    shutil.copy2(src, orig / src.name)
            print("  ok", q_out.name, q_out.stat().st_size)
    finally:
        word.Quit()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
