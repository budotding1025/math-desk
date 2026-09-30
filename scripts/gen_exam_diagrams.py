# -*- coding: utf-8 -*-
"""精确绘制考前卷图题（算盘/数位表/数线等），输出到 printables/_diagrams。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "printables" / "_diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int):
    for name in (
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ):
        p = Path(name)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_abacus_530000(path: Path):
    """十万位 5、万位 3 → 530000，配 50万–60万数线。"""
    W, H = 1400, 900
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f16, f22, f28 = font(22), font(28), font(34)

    # frame
    x0, y0, x1, y1 = 80, 60, 1320, 520
    d.rectangle([x0, y0, x1, y1], outline="#111", width=4)
    beam_y = y0 + 160
    d.line([x0, beam_y, x1, beam_y], fill="#111", width=6)

    # 7 rods: 百万, 十万, 万, 千, 百, 十, 个  — show last 6 meaningful + spare
    labels = ["", "十万", "万", "千", "百", "十", "个"]
    # digit values for rods (index 0 unused left): 0,5,3,0,0,0,0
    digits = [0, 5, 3, 0, 0, 0, 0]
    n = len(labels)
    gap = (x1 - x0) / (n + 1)
    for i, lab in enumerate(labels):
        cx = int(x0 + gap * (i + 1))
        d.line([cx, y0 + 8, cx, y1 - 8], fill="#333", width=3)
        if lab:
            d.text((cx - 22, y0 - 42), lab, fill="#1e7eb8", font=f22)
        # upper deck: one bead (value 5)
        uy = y0 + 45
        # lower deck five beads
        ly = y1 - 40
        dig = digits[i]
        upper_on = dig >= 5
        lower_on = dig % 5
        # upper bead
        if upper_on:
            d.ellipse([cx - 22, beam_y - 55, cx + 22, beam_y - 11], fill="#222", outline="#000")
        else:
            d.ellipse([cx - 22, uy, cx + 22, uy + 44], outline="#000", width=2)
        # lower beads
        for b in range(5):
            if b < lower_on:
                yy = beam_y + 18 + b * 48
                d.ellipse([cx - 22, yy, cx + 22, yy + 44], fill="#222", outline="#000")
            else:
                yy = ly - (4 - b) * 48
                d.ellipse([cx - 22, yy, cx + 22, yy + 44], outline="#000", width=2)

    d.text((80, 545), "算盘表示的数写作：____________________", fill="#111", font=f28)
    # number line
    d.text((80, 620), "在数线上用「↑」标出这个数的大致位置：", fill="#111", font=f22)
    lx0, lx1, ly = 120, 1280, 760
    d.line([lx0, ly, lx1, ly], fill="#111", width=4)
    for i in range(11):
        x = lx0 + int((lx1 - lx0) * i / 10)
        d.line([x, ly - 12, x, ly + 12], fill="#111", width=3)
    d.text((lx0 - 30, ly + 22), "50万", fill="#111", font=f22)
    d.text((lx1 - 40, ly + 22), "60万", fill="#111", font=f22)
    # 学生自标，不预画答案箭头
    im.save(path, quality=95)
    print("wrote", path)


def draw_place_value_51023(path: Path):
    W, H = 1200, 520
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f24, f20 = font(28), font(22)
    heads = ["万位", "千位", "百位", "十位", "个位"]
    counts = [5, 1, 0, 2, 3]
    x0, y0, cell_w, cell_h = 60, 70, 210, 360
    d.text((60, 20), "下图表示五位数 51023（共 11 颗珠）", fill="#111", font=f24)
    for i, (h, c) in enumerate(zip(heads, counts)):
        x = x0 + i * cell_w
        d.rectangle([x, y0, x + cell_w - 10, y0 + cell_h], outline="#111", width=3)
        d.rectangle([x, y0, x + cell_w - 10, y0 + 50], outline="#111", width=3)
        d.text((x + 55, y0 + 10), h, fill="#1e7eb8", font=f24)
        for b in range(c):
            cy = y0 + 80 + b * 48
            d.ellipse([x + 70, cy, x + 130, cy + 42], fill="#222", outline="#000")
        if c == 0:
            d.text((x + 55, y0 + 160), "（空）", fill="#888", font=f20)
    im.save(path, quality=95)
    print("wrote", path)


def draw_numline_M(path: Path):
    W, H = 1200, 320
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f22 = font(26)
    lx0, lx1, ly = 80, 1120, 160
    d.line([lx0, ly, lx1, ly], fill="#111", width=4)
    labels = [(0, "50000"), (0.5, "60000"), (1.0, "70000")]
    for t, lab in labels:
        x = lx0 + int((lx1 - lx0) * t)
        d.line([x, ly - 14, x, ly + 14], fill="#111", width=3)
        d.text((x - 40, ly + 22), lab, fill="#111", font=f22)
    # mid ticks
    for t in (0.25, 0.75):
        x = lx0 + int((lx1 - lx0) * t)
        d.line([x, ly - 8, x, ly + 8], fill="#444", width=2)
    # M near 67000 => between 0.5 and 1.0 at 0.7
    mx = lx0 + int((lx1 - lx0) * 0.7)
    d.ellipse([mx - 8, ly - 8, mx + 8, ly + 8], fill="#111")
    d.text((mx - 12, ly - 50), "M", fill="#1e7eb8", font=f22)
    im.save(path, quality=95)
    print("wrote", path)


def draw_mc_120000(path: Path):
    W, H = 1400, 1000
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f20, f24 = font(22), font(26)

    # ① counter
    d.text((40, 20), "①", fill="#111", font=f24)
    labels = ["十万", "万", "千", "百", "十", "个"]
    beads = [1, 2, 0, 0, 0, 0]
    for i, (lab, c) in enumerate(zip(labels, beads)):
        x = 80 + i * 100
        d.line([x, 70, x, 260], fill="#333", width=3)
        d.text((x - 22, 270), lab, fill="#1e7eb8", font=f20)
        for b in range(c):
            yy = 200 - b * 40
            d.ellipse([x - 18, yy, x + 18, yy + 36], fill="#222")

    # ② grid
    d.text((40, 320), "② 每小格表示 1000", fill="#111", font=f24)
    gx0, gy0 = 80, 370
    cols, rows = 12, 10
    s = 28
    for r in range(rows):
        for c in range(cols):
            x = gx0 + c * s
            y = gy0 + r * s
            d.rectangle([x, y, x + s - 2, y + s - 2], outline="#111", width=1)

    # ③ number line correct 12万
    d.text((40, 680), "③", fill="#111", font=f24)
    lx0, lx1, ly = 100, 700, 760
    d.line([lx0, ly, lx1, ly], fill="#111", width=3)
    for i in range(11):
        x = lx0 + int((lx1 - lx0) * i / 10)
        d.line([x, ly - 8, x, ly + 8], fill="#111", width=2)
    d.text((lx0 - 20, ly + 14), "10万", fill="#111", font=f20)
    d.text((lx1 - 30, ly + 14), "20万", fill="#111", font=f20)
    ax = lx0 + int((lx1 - lx0) * 0.2)
    d.text((ax - 8, ly - 40), "↓", fill="#c00", font=f24)

    # ④ expression
    d.text((780, 720), "④  1×100000＋2×10000", fill="#111", font=f24)

    # note wrong alternative for teacher
    d.text((40, 850), "（对照原卷：不正确项多为数线指在 10万与20万正中≈15万）", fill="#1e7eb8", font=f20)

    im.save(path, quality=95)
    print("wrote", path)


def draw_u5_lines(path: Path):
    W, H = 1400, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f24 = font(28)
    specs = [
        ("①", "parallel_h"),
        ("②", "cross"),
        ("③", "will_meet"),
        ("④", "parallel_d"),
        ("⑤", "perp"),
    ]
    for i, (lab, kind) in enumerate(specs):
        cx = 140 + i * 260
        cy = 220
        d.text((cx - 20, 30), lab, fill="#1e7eb8", font=f24)
        if kind == "parallel_h":
            d.line([cx - 70, cy - 30, cx + 70, cy - 30], fill="#111", width=4)
            d.line([cx - 70, cy + 30, cx + 70, cy + 30], fill="#111", width=4)
        elif kind == "cross":
            d.line([cx - 60, cy - 50, cx + 60, cy + 50], fill="#111", width=4)
            d.line([cx - 60, cy + 50, cx + 60, cy - 50], fill="#111", width=4)
        elif kind == "will_meet":
            d.line([cx - 70, cy + 40, cx + 70, cy + 40], fill="#111", width=4)
            d.line([cx - 40, cy - 50, cx + 50, cy + 10], fill="#111", width=4)
        elif kind == "parallel_d":
            d.line([cx - 50, cy + 50, cx + 50, cy - 50], fill="#111", width=4)
            d.line([cx - 20, cy + 60, cx + 80, cy - 40], fill="#111", width=4)
        elif kind == "perp":
            d.line([cx - 70, cy, cx + 70, cy], fill="#111", width=4)
            d.line([cx, cy - 70, cx, cy + 70], fill="#111", width=4)
            d.rectangle([cx, cy - 18, cx + 18, cy], outline="#111", width=2)
    im.save(path, quality=95)
    print("wrote", path)


def draw_u5_shapes(path: Path):
    W, H = 1400, 700
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f22 = font(24)

    def paren(x, y):
        d.text((x, y), "（　　）", fill="#111", font=f22)

    # row1
    # rectangle
    d.rectangle([80, 80, 260, 180], outline="#111", width=3)
    paren(130, 200)
    # parallelogram
    d.polygon([(340, 180), (420, 80), (580, 80), (500, 180)], outline="#111")
    d.line([340, 180, 420, 80], fill="#111", width=3)
    d.line([420, 80, 580, 80], fill="#111", width=3)
    d.line([580, 80, 500, 180], fill="#111", width=3)
    d.line([500, 180, 340, 180], fill="#111", width=3)
    paren(400, 200)
    # right trapezoid
    d.polygon([(660, 180), (660, 80), (820, 80), (900, 180)], outline="#111")
    d.line([660, 180, 660, 80], fill="#111", width=3)
    d.line([660, 80, 820, 80], fill="#111", width=3)
    d.line([820, 80, 900, 180], fill="#111", width=3)
    d.line([900, 180, 660, 180], fill="#111", width=3)
    paren(740, 200)
    # isosceles trapezoid
    d.line([1000, 180, 1080, 80], fill="#111", width=3)
    d.line([1080, 80, 1240, 80], fill="#111", width=3)
    d.line([1240, 80, 1320, 180], fill="#111", width=3)
    d.line([1320, 180, 1000, 180], fill="#111", width=3)
    paren(1100, 200)

    # row2
    d.polygon([(80, 480), (80, 320), (240, 480)], outline="#111")
    d.line([80, 480, 80, 320], fill="#111", width=3)
    d.line([80, 320, 240, 480], fill="#111", width=3)
    d.line([240, 480, 80, 480], fill="#111", width=3)
    paren(110, 500)
    d.ellipse([340, 320, 540, 480], outline="#111", width=3)
    paren(400, 500)
    d.polygon([(700, 400), (780, 300), (860, 400), (780, 500)], outline="#111")
    d.line([700, 400, 780, 300], fill="#111", width=3)
    d.line([780, 300, 860, 400], fill="#111", width=3)
    d.line([860, 400, 780, 500], fill="#111", width=3)
    d.line([780, 500, 700, 400], fill="#111", width=3)
    paren(740, 520)
    d.polygon([(1000, 480), (1080, 320), (1280, 320), (1200, 480)], outline="#111")
    d.line([1000, 480, 1080, 320], fill="#111", width=3)
    d.line([1080, 320, 1280, 320], fill="#111", width=3)
    d.line([1280, 320, 1200, 480], fill="#111", width=3)
    d.line([1200, 480, 1000, 480], fill="#111", width=3)
    paren(1100, 500)

    im.save(path, quality=95)
    print("wrote", path)


def main():
    draw_abacus_530000(OUT / "u1_abacus_numline_exact.jpg")
    draw_place_value_51023(OUT / "u1_place_value_exact.jpg")
    draw_numline_M(OUT / "u1_numline_M_exact.jpg")
    draw_mc_120000(OUT / "u1_mc120000_exact.jpg")
    draw_u5_lines(OUT / "u5_lines_exact.jpg")
    draw_u5_shapes(OUT / "u5_shapes_exact.jpg")
    print("done")


if __name__ == "__main__":
    main()
