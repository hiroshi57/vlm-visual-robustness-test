"""コア（描画・合成・Δ計算）の自己完結テスト。アダプタ不要・clone 直後に緑。"""
from __future__ import annotations

from PIL import Image

from src import distractors
from src.runner import max_delta


def test_all_symbols_render():
    for name in distractors.SYMBOLS:
        img = distractors.draw_symbol(name, size=80)
        assert img.size == (80, 80)
        assert img.mode == "RGBA"
        assert img.getbbox() is not None  # 何か描かれている


def test_rotation_expands_canvas():
    img = distractors.draw_symbol("triangle", size=80, rotation=45)
    assert img.size[0] >= 80


def test_overlay_preserves_base_size(tmp_path):
    base = tmp_path / "base.png"
    Image.new("RGB", (400, 300), (255, 255, 255)).save(base)
    out = distractors.overlay(base, "red_heart", tmp_path / "out.png")
    assert Image.open(out).size == (400, 300)


def test_overlay_changes_pixels(tmp_path):
    base = tmp_path / "base.png"
    Image.new("RGB", (400, 300), (255, 255, 255)).save(base)
    out = distractors.overlay(base, "red_heart", tmp_path / "out.png")
    assert list(Image.open(out).getdata()) != list(Image.open(base).getdata())


def test_max_delta():
    assert max_delta({"a": 1.0}, {"a": 1.0}) == 0.0
    assert max_delta({"a": 1.0, "b": 0.0}, {"a": 0.3, "b": 0.7}) == 0.7
    assert max_delta({"a": 1.0}, {"b": 1.0}) == 1.0


def test_noise_image(tmp_path):
    out = distractors.noise_image((50, 40), tmp_path / "n.png")
    assert Image.open(out).size == (50, 40)
