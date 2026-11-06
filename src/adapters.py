"""対象エージェント呼び出しの差し込み口（ここだけ案件ごとに実装する）。

RunTask は「画像を渡してタスクを n 回実行し、出力ラベルの比率を返す」関数。
    (model: str, image_path: str, n: int) -> dict[str, float]
返り値の比率は合計 1.0 付近（例: {"recursive": 0.0, "iterative": 1.0}）。

案件が決まったら:
    1) 下の例を参考に run_task を 1 つ書く
    2) 環境変数 VLM_RT_ADAPTER="your_module:your_run_task" を設定
       （または config.toml の [adapter] import に書く）
これだけでテストが動く。
"""
from __future__ import annotations

import importlib
import os
from collections import Counter
from typing import Callable, Protocol


class RunTask(Protocol):
    def __call__(self, model: str, image_path: str, n: int) -> dict[str, float]: ...


def proportions(labels: list[str]) -> dict[str, float]:
    """ラベル列 -> 比率 dict。run_task 実装の補助。"""
    if not labels:
        return {}
    c = Counter(labels)
    total = sum(c.values())
    return {k: v / total for k, v in c.items()}


def load_adapter(spec: str | None = None) -> RunTask:
    """'module.path:callable' から run_task を読み込む。

    spec 未指定なら環境変数 VLM_RT_ADAPTER を参照。見つからなければ ValueError。
    """
    spec = spec or os.environ.get("VLM_RT_ADAPTER")
    if not spec:
        raise ValueError(
            "アダプタ未設定: VLM_RT_ADAPTER='module:callable' を設定するか "
            "load_adapter(spec) に渡してください"
        )
    mod_name, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"spec は 'module:callable' 形式: {spec!r}")
    mod = importlib.import_module(mod_name)
    fn: Callable = getattr(mod, attr)
    return fn


# --- 以下は参考実装（コピーして案件用に書き換える） -------------------------

def example_http_adapter(endpoint: str, classify: Callable[[str], str]) -> RunTask:
    """HTTP JSON エンドポイントに画像を投げるエージェントの例。

    endpoint: {"model","image","n"} を受けて {"outputs": [str, ...]} を返す想定
    classify: 生出力テキスト -> ラベル（例: "recursive"/"iterative"）
    """
    import base64
    import json
    import urllib.request

    def run_task(model: str, image_path: str, n: int) -> dict[str, float]:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        payload = json.dumps({"model": model, "image": img_b64, "n": n}).encode()
        req = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return proportions([classify(o) for o in data["outputs"]])

    return run_task
