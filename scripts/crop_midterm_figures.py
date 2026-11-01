# -*- coding: utf-8 -*-
"""Crop midterm figures from upright source pages into figures/ folders."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "_tmp" / "midterm_figs"
A_FIG = ROOT / "printables" / "midterm" / "A-期中综合练习卷" / "figures"
D_FIG = ROOT / "printables" / "midterm" / "D-期中重点练计算和附加卷" / "figures"


def prep(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Sharpness(im).enhance(1.3)
    return im


def crop_frac(im: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    w, h = im.size
    l, t, r, b = box
    return im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def save(im: Image.Image, path: Path, scale: float = 2.2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = prep(im)
    if scale != 1.0:
        out = out.resize(
            (max(1, int(out.width * scale)), max(1, int(out.height * scale))),
            Image.Resampling.LANCZOS,
        )
    out.save(path, quality=93)
    print("OK", path.relative_to(ROOT), out.size)


def ensure_upright() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    pairs = [
        (
            "A7907",
            ROOT
            / "printables/midterm/A-期中综合练习卷/source/IMG_7907-9625d620-f2f8-4f1d-ab40-dec7fe27699c.jpg",
        ),
        (
            "A7908",
            ROOT
            / "printables/midterm/A-期中综合练习卷/source/IMG_7908-d1510128-8029-4903-8415-3ee11e1dc3de.jpg",
        ),
    ]
    for name, src in pairs:
        im = Image.open(src).convert("RGB").rotate(90, expand=True)
        w, h = im.size
        mid = w // 2
        im.crop((0, 0, mid, h)).save(TMP / f"{name}_L.jpg", quality=95)
        im.crop((mid, 0, w, h)).save(TMP / f"{name}_R.jpg", quality=95)
    for i, p in enumerate(
        sorted((ROOT / "printables/midterm/D-期中重点练计算和附加卷/pages").glob("p*.jpg")),
        1,
    ):
        Image.open(p).convert("RGB").save(TMP / f"D_p{i}.jpg", quality=95)


def main() -> None:
    ensure_upright()
    A7907_L = Image.open(TMP / "A7907_L.jpg")
    A7907_R = Image.open(TMP / "A7907_R.jpg")
    A7908_L = Image.open(TMP / "A7908_L.jpg")
    A7908_R = Image.open(TMP / "A7908_R.jpg")
    D2 = Image.open(TMP / "D_p2.jpg")
    D3 = Image.open(TMP / "D_p3.jpg")
    D4 = Image.open(TMP / "D_p4.jpg")

    # tighter crops — diagram only
    save(crop_frac(A7907_L, (0.58, 0.68, 0.95, 0.86)), A_FIG / "a_setsquares.jpg")
    save(crop_frac(A7907_R, (0.62, 0.20, 0.95, 0.36)), A_FIG / "a_plane.jpg")
    save(crop_frac(A7907_R, (0.12, 0.40, 0.72, 0.55)), A_FIG / "a_route.jpg")
    save(crop_frac(A7907_R, (0.10, 0.72, 0.90, 0.86)), A_FIG / "a_fold_abc.jpg")
    save(crop_frac(A7908_L, (0.22, 0.58, 0.72, 0.66)), A_FIG / "a_ray_ab.jpg")
    save(crop_frac(A7908_R, (0.62, 0.10, 0.94, 0.26)), A_FIG / "a_plates.jpg")
    save(crop_frac(A7908_R, (0.62, 0.36, 0.94, 0.50)), A_FIG / "a_door.jpg")
    save(crop_frac(A7908_R, (0.42, 0.78, 0.94, 0.93)), A_FIG / "a_books.jpg")

    save(crop_frac(D2, (0.62, 0.03, 0.95, 0.16)), D_FIG / "d_reflect.jpg")
    save(crop_frac(D2, (0.10, 0.52, 0.90, 0.66)), D_FIG / "d_draw120.jpg")
    save(crop_frac(D3, (0.10, 0.26, 0.90, 0.36)), D_FIG / "d_points_ab.jpg")
    save(crop_frac(D3, (0.08, 0.42, 0.92, 0.58)), D_FIG / "d_angles123.jpg")
    save(crop_frac(D4, (0.18, 0.48, 0.85, 0.60)), D_FIG / "d_printers.jpg")


if __name__ == "__main__":
    main()
