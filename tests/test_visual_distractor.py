"""視覚ディストラクタ堅牢性テスト（本番）。

VLM_RT_ADAPTER と fixtures/task_clean.png が揃うと有効化される。
未設定なら conftest の fixture が skip する。

根拠: arXiv:2610.36449
"""
from __future__ import annotations

import pytest

from src import distractors
from src.runner import DELTA_THRESHOLD, run_robustness

# 使うモデル（案件に合わせて増減）。アダプタ側が解釈できる識別子。
MODELS = ["default"]


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("symbol", distractors.SYMBOLS)
def test_distractor_does_not_steer(adapter, base_image, model, symbol, tmp_path):
    baseline = adapter(model, base_image, 20)
    polluted_img = distractors.overlay(
        base_image, symbol, tmp_path / f"{symbol}.png"
    )
    polluted = adapter(model, polluted_img, 20)

    from src.runner import max_delta

    delta = max_delta(baseline, polluted)
    assert delta < DELTA_THRESHOLD, (
        f"{model} が無関係シンボル '{symbol}' に影響された "
        f"(Δ={delta:.2f} >= {DELTA_THRESHOLD}) "
        f"baseline={baseline} polluted={polluted}"
    )


@pytest.mark.parametrize("model", MODELS)
def test_full_report(adapter, base_image, model, tmp_path):
    """全シンボルを一括で回し、1 つでも誘導されたら FAIL（詳細レポート付き）。"""
    from src.runner import format_report

    result = run_robustness(adapter, model, base_image, out_dir=tmp_path)
    assert result.passed, "\n" + format_report(result)
