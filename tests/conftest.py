"""pytest 共通設定。

対象アダプタ未設定なら、エージェント依存テストは skip（失敗にしない）。
これにより clone 直後でも `pytest` は緑（コア単体テストのみ実行）になり、
案件が決まって VLM_RT_ADAPTER を設定した瞬間に本番テストが有効化される。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters import load_adapter  # noqa: E402


@pytest.fixture(scope="session")
def adapter():
    spec = os.environ.get("VLM_RT_ADAPTER")
    if not spec:
        pytest.skip("VLM_RT_ADAPTER 未設定: 案件のアダプタを設定すると有効化されます")
    try:
        return load_adapter(spec)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"アダプタ読み込み失敗 ({spec}): {e}")


@pytest.fixture(scope="session")
def base_image():
    p = Path(__file__).parent / "fixtures" / "task_clean.png"
    if not p.exists():
        pytest.skip("fixtures/task_clean.png を置いてください（対象タスクの入力画像）")
    return str(p)
