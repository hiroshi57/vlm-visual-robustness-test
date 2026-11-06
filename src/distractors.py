"""無関係な視覚シンボル（ディストラクタ）の描画と重畳。

案件非依存。対象エージェントが何であっても、ここで作った汚染画像を入力に使う。
根拠: arXiv:2610.36449（単純な視覚シンボルが無関係タスクで VLM 挙動を変える）。

主な関数:
    draw_symbol(name, size, color, rotation) -> RGBA の単体シンボル画像
    overlay(base, name, out_path, ...)       -> ベース画像にシンボルを重畳して保存
    noise_image(size, out_path)              -> ネガティブコントロール（ガウスノイズ）
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

# 論文で強い誘導が報告された最低限のシンボル集合。
SYMBOLS: list[str] = [
    "red_heart",
    "yellow_checkmark",
    "triangle",
    "circle",
    "spiral",
    "branching_arrow",
    "plus",
    "right_arrow",
]

# 既定色（シンボル名に色が含まれる場合はそれを優先）。
_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (220, 40, 40),
    "yellow": (240, 200, 20),
    "blue": (40, 90, 220),
    "pink": (240, 120, 180),
    "green": (40, 180, 90),
    "cyan": (40, 200, 210),
    "purple": (150, 60, 200),
    "black": (20, 20, 20),
}

_DEFAULT_COLOR = {
    "red_heart": "red",
    "yellow_checkmark": "yellow",
}


def _resolve_color(name: str, color: str | None) -> tuple[int, int, int]:
    if color:
        return _NAMED_COLORS.get(color, _NAMED_COLORS["red"])
    return _NAMED_COLORS[_DEFAULT_COLOR.get(name, "red")]


def draw_symbol(
    name: str,
    size: int = 96,
    color: str | None = None,
    rotation: int = 0,
) -> Image.Image:
    """透明背景の RGBA シンボル画像を返す。"""
    base = name.replace("red_", "").replace("yellow_", "")
    rgb = _resolve_color(name, color)
    fill = rgb + (255,)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = size // 10  # margin
    w = max(4, size // 12)  # stroke width

    if base == "heart":
        r = (size - 2 * m) // 4
        cy = size // 2 - r // 2
        d.ellipse([m, cy - r, m + 2 * r, cy + r], fill=fill)
        d.ellipse([size - m - 2 * r, cy - r, size - m, cy + r], fill=fill)
        d.polygon([(m, cy), (size - m, cy), (size // 2, size - m)], fill=fill)
    elif base == "checkmark":
        d.line([(m, size // 2), (size // 2 - m // 2, size - m), (size - m, m)],
               fill=fill, width=w, joint="curve")
    elif base == "triangle":
        d.polygon([(size // 2, m), (m, size - m), (size - m, size - m)], fill=fill)
    elif base == "circle":
        d.ellipse([m, m, size - m, size - m], fill=fill)
    elif base == "plus":
        c = size // 2
        d.rectangle([c - w, m, c + w, size - m], fill=fill)
        d.rectangle([m, c - w, size - m, c + w], fill=fill)
    elif base == "right_arrow":
        c = size // 2
        d.line([(m, c), (size - m - size // 5, c)], fill=fill, width=w)
        d.polygon([(size - m, c), (size - m - size // 4, c - size // 6),
                   (size - m - size // 4, c + size // 6)], fill=fill)
    elif base == "branching_arrow":
        c = size // 2
        d.line([(m, c), (c, c)], fill=fill, width=w)
        for dy in (-1, 1):
            tip = (size - m, c + dy * (size // 3))
            d.line([(c, c), tip], fill=fill, width=w)
            d.ellipse([tip[0] - w, tip[1] - w, tip[0] + w, tip[1] + w], fill=fill)
    elif base == "spiral":
        pts = []
        turns, steps = 3.0, 240
        for i in range(steps + 1):
            t = i / steps
            ang = t * turns * 2 * math.pi
            rad = t * (size // 2 - m)
            pts.append((size // 2 + rad * math.cos(ang),
                        size // 2 + rad * math.sin(ang)))
        d.line(pts, fill=fill, width=max(3, w // 2), joint="curve")
    else:
        raise ValueError(f"unknown symbol: {name}")

    if rotation:
        img = img.rotate(rotation, expand=True, resample=Image.BICUBIC)
    return img


def overlay(
    base: str | Path,
    name: str,
    out_path: str | Path,
    position: str = "top-right",
    size_frac: float = 0.18,
    color: str | None = None,
    rotation: int = 0,
    margin_frac: float = 0.03,
) -> str:
    """ベース画像の隅にシンボルを重畳して out_path に保存し、そのパスを返す。

    position: top-left | top-right | bottom-left | bottom-right | center
    size_frac: シンボルの一辺をベース短辺に対する比率で指定
    """
    bg = Image.open(base).convert("RGBA")
    bw, bh = bg.size
    sym_size = max(24, int(min(bw, bh) * size_frac))
    sym = draw_symbol(name, size=sym_size, color=color, rotation=rotation)
    sw, sh = sym.size
    mg = int(min(bw, bh) * margin_frac)

    pos = {
        "top-left": (mg, mg),
        "top-right": (bw - sw - mg, mg),
        "bottom-left": (mg, bh - sh - mg),
        "bottom-right": (bw - sw - mg, bh - sh - mg),
        "center": ((bw - sw) // 2, (bh - sh) // 2),
    }[position]

    bg.alpha_composite(sym, pos)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out_path)
    return str(out_path)


def noise_image(size: tuple[int, int], out_path: str | Path, seed: int = 0) -> str:
    """ガウスノイズ画像（ネガティブコントロール）を保存。"""
    rng = random.Random(seed)
    w, h = size
    img = Image.new("RGB", (w, h))
    img.putdata([(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
                 for _ in range(w * h)])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return str(out_path)
