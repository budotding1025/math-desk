# -*- coding: utf-8 -*-
"""补全考前卷缺图：U2 角 / U3·U4 竖式箭头 / U5 圆规·梯形运动·作图底图。"""
from __future__ import annotations

import math
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


def blank(w, h="white"):
    return Image.new("RGB", (w, h if isinstance(h, int) else 400), "white" if h == "white" else h)


def save(im: Image.Image, path: Path):
    im.save(path, quality=95)
    print("wrote", path.name)


def arrow_down(d, x, y, size=18, fill="#111"):
    d.polygon([(x, y + size), (x - size // 2, y), (x + size // 2, y)], fill=fill)


def ray(d, ox, oy, ang_deg, length, width=3, fill="#111", head=True):
    rad = math.radians(ang_deg)
    x2 = ox + length * math.cos(rad)
    y2 = oy - length * math.sin(rad)
    d.line([(ox, oy), (x2, y2)], fill=fill, width=width)
    if head:
        # small arrow tip
        left = math.radians(ang_deg + 150)
        right = math.radians(ang_deg - 150)
        tip = (x2, y2)
        p1 = (x2 + 14 * math.cos(left), y2 - 14 * math.sin(left))
        p2 = (x2 + 14 * math.cos(right), y2 - 14 * math.sin(right))
        d.polygon([tip, p1, p2], fill=fill)
    return x2, y2


# ——— U2 ———
def draw_u2_degree_ray(path: Path):
    """0°–90°–180° 数线，箭头指 90°（直角）。"""
    W, H = 1200, 280
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(28)
    y = 120
    x0, x1 = 80, 1100
    d.line([(x0, y), (x1, y)], fill="#111", width=4)
    # arrow tip
    d.polygon([(x1, y), (x1 - 22, y - 12), (x1 - 22, y + 12)], fill="#111")
    ticks = [(0, "0°"), (0.5, "90°"), (1.0, "180°")]
    for t, lab in ticks:
        x = x0 + int((x1 - x0 - 40) * t)
        d.line([(x, y - 16), (x, y + 16)], fill="#111", width=3)
        tw = d.textlength(lab, font=f)
        d.text((x - tw / 2, y + 28), lab, fill="#111", font=f)
    # down arrow at 90°
    x90 = x0 + int((x1 - x0 - 40) * 0.5)
    arrow_down(d, x90, y - 55, 22)
    # room for 周角 mark beyond 180
    d.text((x1 - 180, 40), "（在合适位置标 △ 表周角）", fill="#1e7eb8", font=font(22))
    save(im, path)


def draw_u2_9sector(path: Path):
    W, H = 700, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)
    cx, cy, r = 340, 340, 260
    # semicircle upper
    bbox = [cx - r, cy - r, cx + r, cy + r]
    d.arc(bbox, 180, 0, fill="#111", width=4)
    d.line([(cx - r, cy), (cx + r, cy)], fill="#111", width=4)
    for i in range(10):
        ang = 180 - i * 20  # from left to right
        rad = math.radians(ang)
        d.line([(cx, cy), (cx + r * math.cos(rad), cy - r * math.sin(rad))], fill="#111", width=2)
    # mark ∠1 spanning 2 sectors from right (0° and 20°)
    # right baseline is 0° in math coords = ang 0 from +x; our semicircle: right end = 0°
    for a in (0, 20):
        rad = math.radians(a)
        d.line([(cx, cy), (cx + r * 0.55 * math.cos(rad), cy - r * 0.55 * math.sin(rad))], fill="#111", width=3)
    # arc mark
    d.arc([cx - 70, cy - 70, cx + 70, cy + 70], -20, 0, fill="#111", width=3)
    d.text((cx + 80, cy - 55), "∠1", fill="#111", font=f)
    save(im, path)


def draw_u2_toll(path: Path):
    W, H = 1100, 320
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(22)

    def booth(x, arm_ang, label):
        # vertical pole
        d.line([(x, 80), (x, 250)], fill="#111", width=5)
        d.rectangle([x - 18, 250, x + 18, 270], outline="#111", width=2)
        # arm from top of pole
        rad = math.radians(arm_ang)
        L = 110
        x2 = x + L * math.cos(rad)
        y2 = 80 - L * math.sin(rad)
        d.line([(x, 80), (x2, y2)], fill="#111", width=5)
        d.ellipse([x - 8, 72, x + 8, 88], outline="#111", width=2)
        d.text((x - 20, 280), label, fill="#1e7eb8", font=f)

    # arm angles relative to +x: 0=horiz right, 90=up
    booth(180, 0, "①水平")
    booth(480, 45, "②升起中")
    booth(780, 90, "③竖直")
    d.text((40, 20), "收费亭转杆与竖杆夹角变化示意", fill="#111", font=font(24))
    save(im, path)


def draw_u2_chairs(path: Path):
    W, H = 1200, 340
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(24)

    def chair(x, back_ang, lab):
        # seat
        d.line([(x, 200), (x + 100, 200)], fill="#111", width=4)
        # legs
        d.line([(x + 10, 200), (x + 10, 260)], fill="#111", width=3)
        d.line([(x + 90, 200), (x + 90, 260)], fill="#111", width=3)
        # back from left of seat
        rad = math.radians(back_ang)
        L = 90
        # angle measured from seat (0=along seat right, 90=up, >90 reclined)
        x2 = x + L * math.cos(math.radians(back_ang))
        y2 = 200 - L * math.sin(math.radians(back_ang))
        d.line([(x, 200), (x2, y2)], fill="#111", width=4)
        d.text((x + 30, 280), lab, fill="#1e7eb8", font=f)
        if lab == "①":
            d.text((x + 105, 185), "椅面", fill="#555", font=font(18))
            d.text((x2 - 10, y2 - 25), "椅背", fill="#555", font=font(18))

    # back angles from positive x: acute ~60, right 90, ~108, ~135
    chair(80, 60, "①")
    chair(380, 90, "②")
    chair(680, 108, "③")
    chair(980, 135, "④")
    save(im, path)


def draw_u2_fold_rect(path: Path):
    W, H = 700, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)
    # rectangle
    x0, y0, x1, y1 = 120, 80, 520, 320
    d.rectangle([x0, y0, x1, y1], outline="#111", width=3)
    # fold: bottom-left corner folded up — dashed original corner
    # fold line from bottom side to right side
    fx, fy = x0 + 160, y1  # on bottom
    # actually typical: fold bottom-left so crease from bottom edge to left? 
    # From description: fold from bottom-right corner - angle at bottom-right between bottom and fold
    # Fold line from bottom-right going up-left
    d.line([(x1, y1), (x0 + 80, y0 + 40)], fill="#111", width=3)
    # dashed triangle for folded flap original
    d.line([(x1, y1), (x1, y0 + 100)], fill="#888", width=2)
    # angle mark at bottom-right
    d.arc([x1 - 50, y1 - 50, x1 + 50, y1 + 50], 180, 240, fill="#111", width=2)
    d.text((x1 - 90, y1 - 70), "∠1", fill="#111", font=f)
    # fold arrow
    d.arc([x0 + 200, y0 + 80, x0 + 340, y0 + 220], 200, 320, fill="#4ba3d9", width=2)
    save(im, path)


def draw_u2_ski(path: Path):
    W, H = 1000, 400
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(24)
    d.line([(60, 320), (940, 320)], fill="#111", width=4)
    d.text((460, 340), "地面", fill="#111", font=f)
    # beginner 10°
    L1 = 280
    a1 = math.radians(10)
    d.line([(120, 320), (120 + L1 * math.cos(a1), 320 - L1 * math.sin(a1))], fill="#111", width=4)
    d.line([(120 + L1 * math.cos(a1), 320 - L1 * math.sin(a1)), (120 + L1 * math.cos(a1), 320)], fill="#111", width=2)
    d.arc([120 - 50, 320 - 50, 120 + 50, 320 + 50], -10, 0, fill="#111", width=2)
    d.text((175, 290), "10°", fill="#111", font=font(20))
    d.text((200, 200), "初级道", fill="#1e7eb8", font=f)
    # advanced steeper ~40° with ?
    L2 = 260
    a2 = math.radians(40)
    bx = 560
    d.line([(bx, 320), (bx + L2 * math.cos(a2), 320 - L2 * math.sin(a2))], fill="#111", width=4)
    d.line([(bx + L2 * math.cos(a2), 320 - L2 * math.sin(a2)), (bx + L2 * math.cos(a2), 320)], fill="#111", width=2)
    d.arc([bx - 55, 320 - 55, bx + 55, 320 + 55], -40, 0, fill="#111", width=2)
    d.text((bx + 70, 270), "?", fill="#111", font=font(28))
    d.text((bx + 100, 160), "高级道", fill="#1e7eb8", font=f)
    save(im, path)


def draw_u2_measure_angles(path: Path):
    W, H = 1100, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)
    # ∠1 acute ~50°
    ox, oy = 220, 300
    ray(d, ox, oy, 0, 200, head=True)
    ray(d, ox, oy, 50, 200, head=True)
    d.arc([ox - 45, oy - 45, ox + 45, oy + 45], -50, 0, fill="#111", width=2)
    d.text((ox + 55, oy - 35), "∠1", fill="#111", font=f)
    d.text((ox - 30, 350), "锐角", fill="#1e7eb8", font=font(22))
    # ∠2 obtuse ~130°
    ox2, oy2 = 720, 300
    ray(d, ox2, oy2, 0, 200, head=True)
    ray(d, ox2, oy2, 130, 200, head=True)
    d.arc([ox2 - 45, oy2 - 45, ox2 + 45, oy2 + 45], -130, 0, fill="#111", width=2)
    d.text((ox2 + 40, oy2 - 80), "∠2", fill="#111", font=f)
    d.text((ox2 - 30, 350), "钝角", fill="#1e7eb8", font=font(22))
    save(im, path)


def draw_u2_draw_boxes(path: Path):
    W, H = 1100, 380
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)
    d.rectangle([60, 60, 500, 320], outline="#9bb8cc", width=2)
    d.text((80, 30), "(1) 画出 50° 的角", fill="#111", font=f)
    d.rectangle([580, 60, 1020, 320], outline="#9bb8cc", width=2)
    d.text((600, 30), "(2) 画出 150° 的角", fill="#111", font=f)
    save(im, path)


def draw_u2_circle_fold(path: Path):
    W, H = 1200, 360
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(20)
    specs = [
        (150, "整圆", "360°（周角）", "full"),
        (450, "对折一次", "（　　）°（　　）角", "half"),
        (750, "再对折", "（　　）°（　　）角", "quarter"),
        (1050, "再对折", "（　　）°（　　）角", "eighth"),
    ]
    for i, (cx, title, sub, kind) in enumerate(specs):
        cy, r = 160, 70
        if kind == "full":
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#111", width=3)
            d.line([(cx, cy), (cx + r, cy)], fill="#111", width=2)
        elif kind == "half":
            d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 0, outline="#111", width=3)
            d.line([(cx - r, cy), (cx + r, cy)], fill="#111", width=3)
        elif kind == "quarter":
            d.pieslice([cx - r, cy - r, cx + r, cy + r], 270, 0, outline="#111", width=3)
            d.line([(cx, cy), (cx, cy - r)], fill="#111", width=2)
            d.line([(cx, cy), (cx + r, cy)], fill="#111", width=2)
        else:
            d.pieslice([cx - r, cy - r, cx + r, cy + r], 315, 0, outline="#111", width=3)
            d.line([(cx, cy), (cx + r, cy)], fill="#111", width=2)
            rad = math.radians(45)
            d.line([(cx, cy), (cx + r * math.cos(rad), cy - r * math.sin(rad))], fill="#111", width=2)
        d.text((cx - 40, 250), title, fill="#1e7eb8", font=f)
        d.text((cx - 70, 285), sub, fill="#111", font=f)
        if i < 3:
            d.polygon([(cx + 90, cy), (cx + 110, cy - 10), (cx + 110, cy + 10)], fill="#4ba3d9")
    save(im, path)


def draw_u2_set_squares(path: Path):
    W, H = 1100, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(22)
    # 45-45-90
    pts = [(120, 320), (320, 320), (120, 120)]
    d.polygon(pts, outline="#111")
    for a, b in zip(pts, pts[1:] + pts[:1]):
        d.line([a, b], fill="#111", width=3)
    d.ellipse([190, 200, 230, 240], outline="#111", width=2)
    d.text((95, 330), "（　）", fill="#111", font=f)
    d.text((300, 330), "（　）", fill="#111", font=f)
    d.text((40, 110), "（　）", fill="#111", font=f)
    # 30-60-90
    pts2 = [(520, 320), (820, 320), (820, 140)]
    d.line([pts2[0], pts2[1]], fill="#111", width=3)
    d.line([pts2[1], pts2[2]], fill="#111", width=3)
    d.line([pts2[2], pts2[0]], fill="#111", width=3)
    d.ellipse([700, 240, 740, 280], outline="#111", width=2)
    d.text((500, 330), "（　）", fill="#111", font=f)
    d.text((800, 330), "（　）", fill="#111", font=f)
    d.text((830, 130), "（　）", fill="#111", font=f)
    d.text((100, 40), "填出三角尺上每个角的度数", fill="#111", font=font(24))
    save(im, path)


def draw_u2_compose_angles(path: Path):
    W, H = 1200, 380
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(24)
    # ∠1 = 90+45
    ox, oy = 180, 280
    ray(d, ox, oy, 0, 140, head=False)
    ray(d, ox, oy, 90, 140, head=False)
    ray(d, ox, oy, 135, 140, head=False)
    d.arc([ox - 40, oy - 40, ox + 40, oy + 40], -135, 0, fill="#111", width=2)
    d.text((ox + 50, oy - 50), "∠1", fill="#111", font=f)
    d.text((ox - 40, 320), "∠1＝（　　）°", fill="#111", font=font(20))
    # ∠2 = 60+45? or 60-45 — clean text says 60+45
    ox2, oy2 = 560, 280
    ray(d, ox2, oy2, 0, 140, head=False)
    ray(d, ox2, oy2, 45, 140, head=False)
    ray(d, ox2, oy2, 105, 140, head=False)
    d.arc([ox2 - 40, oy2 - 40, ox2 + 40, oy2 + 40], -105, 0, fill="#111", width=2)
    d.text((ox2 + 50, oy2 - 50), "∠2", fill="#111", font=f)
    d.text((ox2 - 40, 320), "∠2＝（　　）°", fill="#111", font=font(20))
    # ∠3 composite
    ox3, oy3 = 940, 280
    ray(d, ox3, oy3, 0, 140, head=False)
    ray(d, ox3, oy3, 75, 140, head=False)
    d.arc([ox3 - 40, oy3 - 40, ox3 + 40, oy3 + 40], -75, 0, fill="#111", width=2)
    d.text((ox3 + 50, oy3 - 40), "∠3", fill="#111", font=f)
    d.text((ox3 - 40, 320), "∠3＝（　　）°", fill="#111", font=font(20))
    save(im, path)


def draw_u2_intersect(path: Path):
    W, H = 1200, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(22)
    # (1) flat + perp + 45 ray
    ox, oy = 220, 220
    d.line([(ox - 160, oy), (ox + 160, oy)], fill="#111", width=3)
    d.line([(ox, oy - 140), (ox, oy + 20)], fill="#111", width=3)
    ray(d, ox, oy, 45, 130, head=False)
    d.rectangle([ox, oy - 22, ox + 22, oy], outline="#111", width=2)
    d.text((ox - 55, oy - 50), "∠1", fill="#111", font=f)
    d.text((ox + 30, oy - 90), "∠2", fill="#111", font=f)
    d.text((ox + 55, oy - 35), "∠3", fill="#111", font=f)
    d.text((80, 360), "(1) 已知 ∠2＝45°，∠3＝（　　）°", fill="#111", font=f)
    # (2) two perp + diagonal
    ox2, oy2 = 780, 220
    d.line([(ox2 - 150, oy2), (ox2 + 150, oy2)], fill="#111", width=3)
    d.line([(ox2, oy2 - 150), (ox2, oy2 + 150)], fill="#111", width=3)
    d.line([(ox2 - 120, oy2 + 120), (ox2 + 120, oy2 - 120)], fill="#111", width=3)
    d.rectangle([ox2 - 22, oy2 - 22, ox2, oy2], outline="#111", width=2)
    d.text((ox2 - 70, oy2 - 70), "∠1", fill="#111", font=f)
    d.text((ox2 - 90, oy2 + 40), "∠2", fill="#111", font=f)
    d.text((ox2 - 40, oy2 + 70), "∠3", fill="#111", font=f)
    d.text((ox2 + 40, oy2 + 40), "∠4", fill="#111", font=f)
    d.text((ox2 + 50, oy2 - 70), "∠5", fill="#111", font=f)
    d.text((520, 360), "(2) 已知 ∠2＝∠3", fill="#111", font=f)
    save(im, path)


def draw_u2_broken_protractor(path: Path):
    W, H = 900, 480
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    cx, cy, r = 450, 380, 300
    # arc from 30 to 150
    d.arc([cx - r, cy - r, cx + r, cy + r], 210, 330, fill="#111", width=4)
    # ticks
    for deg in range(30, 151, 10):
        rad = math.radians(180 - deg)  # map
        # use standard: 0 at right, but protractor 0 left often
        a = math.radians(deg)
        # place 0° at left (180 math), 180 at right (0 math)
        math_ang = 180 - deg
        rr = math.radians(math_ang)
        x1 = cx + (r - 8) * math.cos(rr)
        y1 = cy - (r - 8) * math.sin(rr)
        x0 = cx + (r - 28) * math.cos(rr)
        y0 = cy - (r - 28) * math.sin(rr)
        d.line([(x0, y0), (x1, y1)], fill="#111", width=2)
        if deg % 30 == 0:
            d.text((x1 - 15, y1 - 28), str(deg), fill="#111", font=font(16))
    # jagged bottom break
    jagged = [(cx - 200, cy), (cx - 160, cy + 25), (cx - 100, cy - 5), (cx - 40, cy + 30),
              (cx + 40, cy + 10), (cx + 120, cy + 35), (cx + 200, cy)]
    d.line(jagged, fill="#111", width=3)
    # center cross
    d.line([(cx - 12, cy), (cx + 12, cy)], fill="#111", width=2)
    d.line([(cx, cy - 12), (cx, cy + 12)], fill="#111", width=2)
    d.text((300, 30), "破损量角器（可利用两刻度差画 75°）", fill="#111", font=font(24))
    save(im, path)


def draw_u2_plane_fold(path: Path):
    W, H = 1100, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(24)
    # left square ABCD
    s = 200
    x, y = 80, 100
    d.rectangle([x, y, x + s, y + s], outline="#111", width=3)
    d.line([(x + s // 2, y), (x + s // 2, y + s)], fill="#888", width=2)  # dashed mid - approximate
    for i in range(0, s, 10):
        d.line([(x + s // 2, y + i), (x + s // 2, y + i + 5)], fill="#888", width=2)
    d.text((x - 5, y - 5), "A", fill="#111", font=f)
    d.text((x - 5, y + s), "B", fill="#111", font=f)
    d.text((x + s, y + s), "C", fill="#111", font=f)
    d.text((x + s, y - 5), "D", fill="#111", font=f)
    d.polygon([(x + s + 40, y + s // 2), (x + s + 70, y + s // 2 - 12), (x + s + 70, y + s // 2 + 12)], fill="#4ba3d9")
    # right folded: B,C to G on midline
    x2, y2 = 520, 100
    d.rectangle([x2, y2, x2 + s, y2 + s], outline="#111", width=3)
    g = (x2 + s // 2, y2 + s // 2 + 40)
    d.ellipse([g[0] - 4, g[1] - 4, g[0] + 4, g[1] + 4], fill="#111")
    d.text((g[0] + 8, g[1]), "G", fill="#111", font=f)
    d.line([(x2, y2), g], fill="#111", width=3)  # A-G
    d.line([(x2 + s, y2), g], fill="#111", width=3)  # D-G
    # dashed original B C folds
    d.line([(x2, y2 + s), g], fill="#888", width=2)
    d.line([(x2 + s, y2 + s), g], fill="#888", width=2)
    d.text((x2 - 5, y2 - 5), "A", fill="#111", font=f)
    d.text((x2 + s, y2 - 5), "D", fill="#111", font=f)
    d.arc([g[0] - 35, g[1] - 35, g[0] + 35, g[1] + 35], 200, 270, fill="#111", width=2)
    d.text((g[0] - 55, g[1] - 50), "∠1", fill="#111", font=f)
    d.arc([g[0] - 45, g[1] - 45, g[0] + 45, g[1] + 45], 40, 140, fill="#111", width=2)
    d.text((g[0] - 15, g[1] + 50), "∠2", fill="#111", font=f)
    d.text((200, 360), "已知 ∠1＝60°，求 ∠2", fill="#111", font=f)
    save(im, path)


def draw_u2_kites(path: Path):
    W, H = 1100, 480
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(24)
    d.line([(60, 400), (1040, 400)], fill="#111", width=4)
    pts = [("甲", 200, 55), ("乙", 500, 40), ("丙", 800, None)]
    for name, x, ang in pts:
        d.ellipse([x - 5, 395, x + 5, 405], fill="#111")
        d.text((x - 12, 420), name, fill="#111", font=f)
        if ang is not None:
            L = 280
            rad = math.radians(ang)
            kx = x + L * math.cos(rad)
            ky = 400 - L * math.sin(rad)
            d.line([(x, 400), (kx, ky)], fill="#111", width=3)
            # kite diamond
            d.polygon([(kx, ky - 28), (kx + 18, ky), (kx, ky + 28), (kx - 18, ky)], outline="#111")
            d.line([(kx, ky - 28), (kx, ky + 28)], fill="#111", width=2)
            d.arc([x - 40, 400 - 40, x + 40, 400 + 40], -ang, 0, fill="#111", width=2)
    d.text((120, 40), "线长相同　（丙处请自画 30° 夹角）", fill="#1e7eb8", font=font(22))
    save(im, path)


# ——— U3 / U4 竖式 ———
def draw_vertical_mul(path: Path, a: str, b: str, rows: list[str], arrow_row: int, box_row: int | None = None, title="", shift_from: int = 1):
    """rows: partial products; from index shift_from, draw one digit-slot left (×10 place)."""
    W, H = 560, 440
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(32)
    x_right = 380
    y = 40
    line_h = 44
    slot = d.textlength("0", font=f)

    def draw_num(s, yy, boxed=False, shift=0):
        tw = d.textlength(s, font=f)
        xx = x_right - tw - shift * slot
        if boxed:
            d.rectangle([xx - 8, yy - 4, xx + tw + 8, yy + 36], outline="#111", width=2)
        d.text((xx, yy), s, fill="#111", font=f)
        return xx, tw

    draw_num(a, y)
    y += line_h
    draw_num("×" + b, y)
    y += line_h
    d.line([(x_right - 220, y), (x_right + 10, y)], fill="#111", width=3)
    y += 10
    for i, row in enumerate(rows):
        sh = 1 if i >= shift_from else 0
        boxed = box_row is not None and i == box_row
        xx, tw = draw_num(row, y, boxed=boxed, shift=sh)
        if i == arrow_row:
            d.polygon([(x_right + 30, y + 16), (x_right + 70, y + 4), (x_right + 70, y + 28)], fill="#111")
            d.text((x_right + 78, y + 2), "←", fill="#111", font=font(28))
        y += line_h
    d.line([(x_right - 220, y), (x_right + 10, y)], fill="#111", width=3)
    if title:
        d.text((40, H - 40), title, fill="#1e7eb8", font=font(20))
    save(im, path)


def draw_u3_114x11(path: Path):
    # 114×11 → 114 + 1140 = 1254; arrow on second partial 114 (tens)
    draw_vertical_mul(path, "114", "11", ["114", "114"], arrow_row=1, title="竖式中箭头所指部分")


def draw_u4_125x23(path: Path):
    # 125×23 → 375 + 2500 = 2875; arrow on second row 250 (as 125×20)
    draw_vertical_mul(path, "125", "23", ["375", "250"], arrow_row=1, title="箭头所指部分积")


def draw_u4_225x12(path: Path):
    draw_vertical_mul(path, "225", "12", ["450", "225"], arrow_row=1, box_row=1, title="方框＋箭头所指一步")


# ——— U5 leftovers ———
def draw_u5_compass(path: Path):
    W, H = 1000, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)

    def compass(x, y, span, lab_l, lab_r):
        # hinge
        d.ellipse([x - 10, y - 10, x + 10, y + 10], outline="#111", width=3)
        # legs
        d.line([(x, y), (x - span // 2, y + 160)], fill="#111", width=4)
        d.line([(x, y), (x + span // 2, y + 160)], fill="#111", width=4)
        d.ellipse([x - span // 2 - 5, y + 155, x - span // 2 + 5, y + 165], fill="#111")
        d.ellipse([x + span // 2 - 5, y + 155, x + span // 2 + 5, y + 165], fill="#111")
        # segment
        d.line([(x - span // 2, y + 180), (x + span // 2, y + 180)], fill="#111", width=3)
        d.text((x - span // 2 - 8, y + 190), lab_l, fill="#111", font=f)
        d.text((x + span // 2 - 8, y + 190), lab_r, fill="#111", font=f)

    compass(250, 60, 140, "A", "B")
    compass(720, 60, 200, "C", "D")
    d.text((180, 20), "比较线段长短（开口越大越长）", fill="#111", font=font(24))
    save(im, path)


def draw_u5_trap_motion(path: Path):
    W, H = 900, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(26)
    # parallel dashed lines
    for y in (120, 300):
        for x in range(80, 820, 16):
            d.line([(x, y), (x + 10, y)], fill="#888", width=2)
    # trapezoid ABCD: A top-left, D top-right, B bot-left, C bot-right
    A, D, C, B = (320, 120), (520, 120), (680, 300), (200, 300)
    d.line([A, D], fill="#111", width=4)
    d.line([D, C], fill="#111", width=4)
    d.line([C, B], fill="#111", width=4)
    d.line([B, A], fill="#111", width=4)
    for p, lab in [(A, "A"), (D, "D"), (B, "B"), (C, "C")]:
        d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill="#111")
        d.text((p[0] + 8, p[1] - 28), lab, fill="#111", font=f)
    # arrow showing D moves left
    d.polygon([(500, 90), (360, 90), (360, 75), (330, 95), (360, 115), (360, 100), (500, 100)], fill="#4ba3d9")
    d.text((200, 350), "AD∥BC，点 D 沿直线向 A 移动", fill="#111", font=font(22))
    save(im, path)


def draw_u5_angle_P(path: Path):
    W, H = 700, 420
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    ox, oy = 120, 320
    ray(d, ox, oy, 15, 420, head=True)
    ray(d, ox, oy, 55, 420, head=True)
    px, py = 320, 220
    d.ellipse([px - 5, py - 5, px + 5, py + 5], fill="#111")
    d.text((px + 10, py - 10), "P", fill="#111", font=font(28))
    d.text((40, 30), "过点 P 分别向角的两边作垂线", fill="#1e7eb8", font=font(22))
    save(im, path)


def draw_u5_line_AB(path: Path):
    W, H = 900, 360
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f = font(28)
    y = 200
    d.line([(60, y), (820, y)], fill="#111", width=4)
    d.text((830, y - 14), "l", fill="#111", font=f)
    d.ellipse([280 - 5, 110 - 5, 280 + 5, 110 + 5], fill="#111")
    d.text((290, 90), "A", fill="#111", font=f)
    d.ellipse([560 - 5, 280 - 5, 560 + 5, 280 + 5], fill="#111")
    d.text((570, 285), "B", fill="#111", font=f)
    d.text((40, 30), "过 A、B 分别作 l 的垂线", fill="#1e7eb8", font=font(22))
    save(im, path)


def main():
    # also re-export core U1/U5 from sibling if needed — only extras here when run alone
    draw_u2_degree_ray(OUT / "u2_degree_ray_exact.jpg")
    draw_u2_9sector(OUT / "u2_9sector_exact.jpg")
    draw_u2_toll(OUT / "u2_toll_exact.jpg")
    draw_u2_chairs(OUT / "u2_chairs_exact.jpg")
    draw_u2_fold_rect(OUT / "u2_fold_rect_exact.jpg")
    draw_u2_ski(OUT / "u2_ski_exact.jpg")
    draw_u2_measure_angles(OUT / "u2_measure_angles_exact.jpg")
    draw_u2_draw_boxes(OUT / "u2_draw_boxes_exact.jpg")
    draw_u2_circle_fold(OUT / "u2_circle_fold_exact.jpg")
    draw_u2_set_squares(OUT / "u2_set_squares_exact.jpg")
    draw_u2_compose_angles(OUT / "u2_compose_angles_exact.jpg")
    draw_u2_intersect(OUT / "u2_intersect_exact.jpg")
    draw_u2_broken_protractor(OUT / "u2_broken_protractor_exact.jpg")
    draw_u2_plane_fold(OUT / "u2_plane_fold_exact.jpg")
    draw_u2_kites(OUT / "u2_kites_exact.jpg")
    draw_u3_114x11(OUT / "u3_114x11_exact.jpg")
    draw_u4_125x23(OUT / "u4_125x23_exact.jpg")
    draw_u4_225x12(OUT / "u4_225x12_exact.jpg")
    draw_u5_compass(OUT / "u5_compass_exact.jpg")
    draw_u5_trap_motion(OUT / "u5_trap_motion_exact.jpg")
    draw_u5_angle_P(OUT / "u5_angle_P_exact.jpg")
    draw_u5_line_AB(OUT / "u5_line_AB_exact.jpg")
    print("done extras")


if __name__ == "__main__":
    main()
