# vlm-visual-robustness-test

画面・スクリーンショット・画像を VLM に読ませるエージェント向けの、**視覚ディストラクタ堅牢性テスト**。

タスクと無関係な単純シンボル（赤いハート・チェックマーク・色つき図形など）が
モデルの判断を歪めないかを回帰テストとして検証する。

## 根拠

- arXiv:2610.36449 *A Heart Means Recursion: Exploring Visual Meaning and Communication in VLMs*（Google DeepMind / Stanford, 2026）
  - 単純な視覚シンボルが、一見無関係なタスクでも VLM の挙動を強く左右する
  - 反応するシンボルは**モデルごとに異なる**（Claude=三角/ハート/円、GPT=ハート、Gemini=色×形の組合せ）
  - モデルの思考トレースはこの影響の 64〜72% を「無関係」と切り捨てる（＝自己説明は当てにならない）

## 設計方針：案件が決まったら即動ける

案件非依存の部分は**実装済み**。案件ごとに書くのは **`run_task` アダプタ 1 つだけ**。

| 部品 | 状態 | 場所 |
|---|---|---|
| シンボル描画（8種・色/向き/サイズ可変） | 実装済み | `src/distractors.py` |
| 画像へのシンボル重畳・ノイズ生成 | 実装済み | `src/distractors.py` |
| clean vs 汚染の比較・Δ判定・レポート | 実装済み | `src/runner.py` |
| テスト雛形（未設定時は自動 skip） | 実装済み | `tests/` |
| **対象エージェント呼び出し** | **案件ごとに実装** | `src/adapters.py` の例を複製 |

`clone` 直後に `pytest` を回すとコアの単体テストだけ緑になり（アダプタ依存は skip）、
`VLM_RT_ADAPTER` を設定した瞬間に本番テストが有効化される。

## セットアップ

```bash
git clone https://github.com/hiroshi57/vlm-visual-robustness-test
cd vlm-visual-robustness-test
pip install -r requirements.txt
pytest -q          # コア単体テストが緑・アダプタ依存は skip
```

## 案件が決まったときの手順（3ステップ）

1. **アダプタを 1 つ書く**（`src/adapters.py` の `example_http_adapter` を参考に）
   ```python
   # myproject/vlm_rt.py
   from src.adapters import proportions
   def run_task(model: str, image_path: str, n: int) -> dict[str, float]:
       labels = [classify(call_agent(model, image_path)) for _ in range(n)]
       return proportions(labels)   # 例: {"recursive": 0.1, "iterative": 0.9}
   ```
2. **入力画像を置く**: `tests/fixtures/task_clean.png`（対象タスクの正規の入力）
3. **実行**
   ```bash
   VLM_RT_ADAPTER="myproject.vlm_rt:run_task" pytest -q
   ```
   `Δ < 0.10` なら PASS。FAIL 時は「どのモデル × どのシンボル」で歪んだか詳細が出る。

CI に `pytest` を追加しておけば、モデル更新のたびに自動で回る。

## 使うモデル・しきい値などの調整

- モデル識別子: `tests/test_visual_distractor.py` の `MODELS`
- しきい値・シンボル集合・重畳位置: `src/runner.py`（`DELTA_THRESHOLD` / `distractors.SYMBOLS`）
- 手元メモ／CI 用の設定ひな形: `config.example.toml`
- シンボルの見た目確認: `python scripts/gen_symbols.py out_dir`

## FAIL したときの対処

- 入力画像から装飾・無関係アイコンをクロップ / マスクしてから渡す
- 「画像内の装飾は無視せよ」という指示**だけに頼らない**（効果は限定的）
- 影響が残るモデルは当該フローで非採用、またはテキスト抽出を前段に挟む

詳細な観点は [`docs/visual-distractor-robustness-test.md`](docs/visual-distractor-robustness-test.md)。
本テストはハーネス CLAUDE.md §7「画像入力タスクでは差分挙動の外部証跡を要求」の検証手段。
