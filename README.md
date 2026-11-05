# vlm-visual-robustness-test

画面・スクリーンショット・画像を VLM に読ませるエージェント向けの、**視覚ディストラクタ堅牢性テスト**。

タスクと無関係な単純シンボル（赤いハート・チェックマーク・色つき図形など）が
モデルの判断を歪めないかを回帰テストとして検証する。

## 根拠

- arXiv:2610.36449 *A Heart Means Recursion: Exploring Visual Meaning and Communication in VLMs*（Google DeepMind / Stanford, 2026）
  - 単純な視覚シンボルが、一見無関係なタスクでも VLM の挙動を強く左右する
  - 反応するシンボルは**モデルごとに異なる**（Claude=三角/ハート/円、GPT=ハート、Gemini=色×形の組合せ）
  - モデルの思考トレースはこの影響の 64〜72% を「無関係」と切り捨てる（＝自己説明は当てにならない）

## 使い方

テスト観点とチェックリストは [`docs/visual-distractor-robustness-test.md`](docs/visual-distractor-robustness-test.md) を参照。
テスト実装のひな形は [`tests/`](tests/) に置く。

## いつ回すか

- スクショ / GUI / 画像を入力に取るエージェント・フローを変更したとき
- 使用モデル（Claude / Gemini / GPT）を差し替え・バージョンアップしたとき
