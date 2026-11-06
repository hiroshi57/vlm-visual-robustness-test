"""シンボル一覧を PNG に書き出して目視確認する補助スクリプト。

    python scripts/gen_symbols.py [out_dir]

案件には不要。描画結果を見たいときだけ使う。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image  # noqa: E402

from src import distractors  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("symbol_preview")
    out.mkdir(parents=True, exist_ok=True)
    for name in distractors.SYMBOLS:
        for rot in (0, 45):
            img = distractors.draw_symbol(name, size=128, rotation=rot)
            canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
            canvas.alpha_composite(img)
            path = out / f"{name}_rot{rot}.png"
            canvas.convert("RGB").save(path)
            print(path)


if __name__ == "__main__":
    main()
