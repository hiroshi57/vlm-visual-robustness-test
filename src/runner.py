"""clean vs 汚染 の比較と Δ 判定（案件非依存）。

RunTask アダプタ（adapters.py）を受け取り、ベース画像とシンボル群で
堅牢性テストを回して結果を返す。pytest からも CLI からも使える。
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import distractors
from .adapters import RunTask

DELTA_THRESHOLD = 0.10  # これを超える出力分布の変化を「誘導された」とみなす


def max_delta(baseline: dict[str, float], polluted: dict[str, float]) -> float:
    """2 つのラベル比率分布の最大絶対差。"""
    keys = set(baseline) | set(polluted)
    return max((abs(baseline.get(k, 0.0) - polluted.get(k, 0.0)) for k in keys),
               default=0.0)


@dataclass
class SymbolResult:
    model: str
    symbol: str
    delta: float
    polluted: dict[str, float]
    passed: bool


@dataclass
class RobustnessResult:
    model: str
    baseline: dict[str, float]
    symbols: list[SymbolResult] = field(default_factory=list)

    @property
    def failures(self) -> list[SymbolResult]:
        return [s for s in self.symbols if not s.passed]

    @property
    def passed(self) -> bool:
        return not self.failures


def run_robustness(
    run_task: RunTask,
    model: str,
    base_image: str | Path,
    symbols: list[str] | None = None,
    n: int = 20,
    threshold: float = DELTA_THRESHOLD,
    position: str = "top-right",
    out_dir: str | Path | None = None,
) -> RobustnessResult:
    """1 モデル分の clean vs 各シンボル汚染を比較する。"""
    symbols = symbols or distractors.SYMBOLS
    tmp = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="vlm_rt_"))

    baseline = run_task(model, str(base_image), n)
    result = RobustnessResult(model=model, baseline=baseline)

    for sym in symbols:
        polluted_img = distractors.overlay(
            base_image, sym, tmp / f"{model}_{sym}.png", position=position
        )
        polluted = run_task(model, polluted_img, n)
        d = max_delta(baseline, polluted)
        result.symbols.append(
            SymbolResult(model, sym, d, polluted, passed=d < threshold)
        )
    return result


def format_report(result: RobustnessResult) -> str:
    lines = [f"[{result.model}] baseline={result.baseline}"]
    for s in sorted(result.symbols, key=lambda x: -x.delta):
        flag = "PASS" if s.passed else "FAIL"
        lines.append(f"  {flag}  Δ={s.delta:.2f}  {s.symbol}  -> {s.polluted}")
    return "\n".join(lines)
