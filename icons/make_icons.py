#!/usr/bin/env python3
"""네온 생존자 앱 아이콘 생성 스크립트.

사용법 (저장소 루트에서):
    python3 icons/make_icons.py

만드는 파일 (모두 icons/ 아래):
    icon-192.png           192x192  (manifest any)
    icon-512.png           512x512  (manifest any)
    icon-maskable-512.png  512x512  (manifest maskable, 안전 영역 80%)
    apple-touch-icon.png   180x180  (iOS 홈 화면, 불투명 배경)

디자인: 어두운 네온 그리드 배경 위에 하늘색으로 빛나는 생존자 얼굴
(보라 고깔모자 + 금색 꼭지 + 빛나는 두 눈). 게임 안 drawPlayer()의 색을 그대로 쓴다.
모든 크기는 4배 슈퍼샘플링 후 LANCZOS로 줄여 그린다. 필요한 것은 Pillow 뿐이다.
"""

import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SS = 4  # supersampling factor

BG_TOP = (13, 11, 30)     # #0d0b1e
BG_BOTTOM = (7, 6, 15)    # #07060f
GRID = (77, 243, 255)     # --cyan
CYAN = (77, 243, 255)
CYAN_HI = (168, 250, 255)
FACE_TOP = (16, 54, 84)   # 몸통 위쪽(빛 받는 면)
FACE_BOTTOM = (5, 16, 29)  # 몸통 아래쪽(어두운 면)
VIOLET = (180, 107, 255)  # --violet (고깔모자)
VIOLET_HI = (214, 170, 255)
GOLD = (255, 216, 77)     # --gold (모자 꼭지)
EYE = (233, 253, 255)


# --------------------------------------------------------------- helpers
def vgrad(size, y0, y1, top, bottom):
    """y0~y1 구간에서 top→bottom 으로 가는 세로 그라디언트 (구간 밖은 양 끝색)."""
    S = size
    col = Image.new("RGB", (1, S))
    for y in range(S):
        t = (y - y0) / max(1.0, y1 - y0)
        t = min(1.0, max(0.0, t))
        col.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return col.resize((S, S), Image.BILINEAR)


def add_glow(base, layer, blur):
    """base(RGBA) 위에 layer(RGB)를 더하기 합성 → 어두운 배경에서 네온처럼 밝아진다."""
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.paste(ImageChops.add(base.convert("RGB"), layer))


def disc(size, cx, cy, r, color):
    img = Image.new("RGB", (size, size), (0, 0, 0))
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return img


def poly(size, pts, color):
    img = Image.new("RGB", (size, size), (0, 0, 0))
    ImageDraw.Draw(img).polygon(pts, fill=color)
    return img


# --------------------------------------------------------------- layers
def radial_background(S):
    """중앙이 밝고 가장자리가 어두운 네온 글로우 배경 (작게 계산 후 확대)."""
    w = 128
    img = Image.new("RGB", (w, w))
    px = img.load()
    c = (w - 1) / 2
    maxd = math.hypot(c, c)
    for y in range(w):
        for x in range(w):
            d = math.hypot(x - c, y - c) / maxd
            k = max(0.0, 1.0 - d) ** 2.2          # 중앙 청록 기운
            v = max(0.0, 1.0 - abs(d - 0.45) * 2.3) ** 2  # 보라 기운 고리
            r = BG_BOTTOM[0] + BG_TOP[0] * 0.35 * (1 - d) + 40 * v * 0.40 + 10 * k
            g = BG_BOTTOM[1] + BG_TOP[1] * 0.35 * (1 - d) + 14 * v * 0.40 + 26 * k
            b = BG_BOTTOM[2] + BG_TOP[2] * 0.35 * (1 - d) + 52 * v * 0.60 + 30 * k
            px[x, y] = (min(255, int(r)), min(255, int(g)), min(255, int(b)))
    return img.resize((S, S), Image.LANCZOS).convert("RGBA")


def draw_grid(base, S):
    """네온 그리드. 가는 선 + 번진 글로우 한 겹."""
    lines = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    step = S / 9.0
    lw = max(1, int(round(S / 420)))
    for i in range(1, 9):
        p = step * i
        a = 46 if i % 3 else 74
        d.line([(p, 0), (p, S)], fill=GRID + (a,), width=lw)
        d.line([(0, p), (S, p)], fill=GRID + (a,), width=lw)
    base.alpha_composite(lines.filter(ImageFilter.GaussianBlur(S / 70)))
    base.alpha_composite(lines)


def draw_character(base, S, maskable):
    """생존자 얼굴: 몸통 원 + 빛나는 두 눈 + 고깔모자(금색 꼭지)."""
    R = (0.218 if maskable else 0.252) * S
    cx = S / 2
    cy = S / 2 + 0.58 * R          # 모자까지 포함한 그림이 세로 가운데 오도록

    top = cy - R
    bot = cy + R
    tip = (cx + 0.16 * R, cy - 1.96 * R)

    # ---- 1. 몸통 뒤 하늘색 후광 ----
    add_glow(base, disc(S, cx, cy, R * 1.55, (0, 34, 46)), R * 0.45)
    add_glow(base, disc(S, cx, cy, R * 1.10, (0, 96, 120)), R * 0.18)

    # ---- 2. 고깔모자 뒤 보라 후광 ----
    hat_pts = [(cx - 1.00 * R, cy - 0.62 * R), (cx + 1.00 * R, cy - 0.62 * R), tip]
    add_glow(base, poly(S, hat_pts, (52, 26, 84)), R * 0.30)

    # ---- 3. 고깔모자 ----
    hat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hat)
    hd.polygon(hat_pts, fill=VIOLET + (255,))
    # 왼쪽에서 빛을 받는 면
    hd.polygon([(cx - 1.00 * R, cy - 0.62 * R), (tip[0], tip[1]),
                (cx - 0.10 * R, cy - 0.62 * R)], fill=VIOLET_HI + (255,))
    hd.line(hat_pts + [hat_pts[0]], fill=(236, 214, 255, 255),
            width=max(2, int(R * 0.075)), joint="curve")
    base.alpha_composite(hat)
    # 모자 테두리 번짐
    edge = Image.new("RGB", (S, S), (0, 0, 0))
    ImageDraw.Draw(edge).line(hat_pts + [hat_pts[0]], fill=(90, 40, 130),
                              width=max(2, int(R * 0.09)), joint="curve")
    add_glow(base, edge, R * 0.10)

    # ---- 4. 모자 꼭지 금색 구슬 ----
    add_glow(base, disc(S, tip[0], tip[1], R * 0.46, (150, 110, 20)), R * 0.20)
    bd = ImageDraw.Draw(base)
    br = 0.215 * R
    bd.ellipse([tip[0] - br, tip[1] - br, tip[0] + br, tip[1] + br], fill=GOLD + (255,))
    bd.ellipse([tip[0] - br * 0.45, tip[1] - br * 0.62, tip[0] + br * 0.12, tip[1] - br * 0.12],
               fill=(255, 246, 190, 230))

    # ---- 5. 몸통 원 (위에서 아래로 어두워지는 남색) ----
    circle = Image.new("L", (S, S), 0)
    ImageDraw.Draw(circle).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    face = vgrad(S, top - 0.15 * R, bot, FACE_TOP, FACE_BOTTOM).convert("RGBA")
    face.putalpha(circle)
    base.alpha_composite(face)

    # ---- 6. 하늘색 테두리 (위쪽이 밝은 그라디언트 링) ----
    ring_w = max(3, int(round(R * 0.135)))
    ring_mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(ring_mask).ellipse([cx - R, cy - R, cx + R, cy + R],
                                      outline=255, width=ring_w)
    ring = vgrad(S, top, bot, CYAN_HI, (36, 170, 196)).convert("RGBA")
    ring.putalpha(ring_mask)
    base.alpha_composite(ring)
    # 테두리 네온 번짐
    ring_glow = Image.new("RGB", (S, S), (0, 0, 0))
    ImageDraw.Draw(ring_glow).ellipse([cx - R, cy - R, cx + R, cy + R],
                                      outline=(20, 120, 145), width=ring_w)
    add_glow(base, ring_glow, R * 0.14)

    # ---- 7. 빛나는 두 눈 ----
    er = 0.195 * R
    eye_grad = vgrad(S, cy - er * 3, cy + er * 2, (246, 255, 255), (120, 232, 250))
    for sx in (-0.355, 0.355):
        ex, ey = cx + sx * R, cy - 0.04 * R
        add_glow(base, disc(S, ex, ey, er * 1.85, (0, 70, 86)), er * 1.10)
        add_glow(base, disc(S, ex, ey, er * 1.15, (0, 150, 178)), er * 0.34)
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse([ex - er * 1.08, ey - er, ex + er * 1.08, ey + er], fill=255)
        eye = eye_grad.convert("RGBA")
        eye.putalpha(mask)
        base.alpha_composite(eye)
        # 눈 가장자리 하늘색 라인
        ImageDraw.Draw(base).ellipse([ex - er * 1.08, ey - er, ex + er * 1.08, ey + er],
                                     outline=(190, 250, 255, 255),
                                     width=max(2, int(er * 0.16)))

    # ---- 8. 입가의 옅은 하늘색 반사광 ----
    refl = Image.new("RGB", (S, S), (0, 0, 0))
    ImageDraw.Draw(refl).ellipse([cx - 0.70 * R, cy + 0.40 * R, cx + 0.70 * R, cy + 0.78 * R],
                                 fill=(0, 52, 66))
    add_glow(base, refl, R * 0.20)


def vignette(base, S):
    m = Image.new("L", (96, 96), 0)
    ImageDraw.Draw(m).ellipse([-14, -14, 110, 110], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(9)).resize((S, S), Image.LANCZOS)
    dark = Image.new("RGBA", (S, S), (3, 2, 8, 255))
    dark.putalpha(Image.eval(m, lambda v: int((255 - v) * 0.5)))
    base.alpha_composite(dark)


def render(size, maskable=False):
    S = size * SS
    base = radial_background(S)
    draw_grid(base, S)
    draw_character(base, S, maskable)
    vignette(base, S)
    return base.convert("RGB").resize((size, size), Image.LANCZOS)


def main():
    jobs = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, False),
    ]
    for name, size, maskable in jobs:
        img = render(size, maskable)
        path = os.path.join(OUT_DIR, name)
        img.save(path, "PNG", optimize=True)
        print("%-24s %3dx%-3d  %7d bytes" % (name, size, size, os.path.getsize(path)))


if __name__ == "__main__":
    main()
