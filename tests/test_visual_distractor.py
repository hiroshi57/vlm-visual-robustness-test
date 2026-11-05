"""視覚ディストラクタ堅牢性テスト（ひな形）

根拠: arXiv:2610.36449
使い方: run_task / render_distractor を各案件のエージェント呼び出しに差し替える。

比較ロジック（baseline vs 汚染）としきい値判定は共通。モデルごとに全シンボルを回す。
"""

import pytest

# --- 各案件側で実装して差し替える 2 つのフック ------------------------------

def run_task(model: str, image_path: str, n: int = 20) -> dict[str, float]:
    """与えた画像でタスクを n 回実行し、出力ラベルの分布（比率）を返す。

    返り値例: {"recursive": 0.0, "iterative": 1.0}
    """
    raise NotImplementedError("各案件のエージェント呼び出しに差し替える")


def render_distractor(base_image: str, symbol: str, out_path: str) -> str:
    """base_image の隅に無関係な視覚シンボルを重畳した画像を out_path に書き出す。"""
    raise NotImplementedError("画像合成処理に差し替える")


# --- テスト設定 --------------------------------------------------------------

MODELS = ["claude", "gemini", "gpt"]

# 最低限の汚染シンボル・セット（配置・向き・色は各案件で振る）
DISTRACTOR_SYMBOLS = [
    "red_heart",
    "yellow_checkmark",
    "colored_triangle",
    "colored_circle",
    "spiral",
    "branching_arrow",
]

# Δ（出力分布の差）の許容しきい値
DELTA_THRESHOLD = 0.10

BASE_IMAGE = "fixtures/task_clean.png"


def _max_delta(baseline: dict[str, float], polluted: dict[str, float]) -> float:
    keys = set(baseline) | set(polluted)
    return max(abs(baseline.get(k, 0.0) - polluted.get(k, 0.0)) for k in keys)


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("symbol", DISTRACTOR_SYMBOLS)
def test_distractor_does_not_steer(model, symbol, tmp_path):
    baseline = run_task(model, BASE_IMAGE)

    polluted_img = render_distractor(
        BASE_IMAGE, symbol, str(tmp_path / f"{symbol}.png")
    )
    polluted = run_task(model, polluted_img)

    delta = _max_delta(baseline, polluted)
    assert delta < DELTA_THRESHOLD, (
        f"{model} が無関係シンボル '{symbol}' に影響された "
        f"(Δ={delta:.2f} >= {DELTA_THRESHOLD})"
    )
