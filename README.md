# kaggriculture-401-silver

Kaggriculture 参戦記録（401位・銀メダル）

Kaggle の Simulation コンペ **Kaggriculture**（2人対戦の農場経営エージェント競技）の参戦記録です。
最終順位は **401位（銀メダル）、公開スコア 2185.6** でした。

> English summary: This repository documents my entry to the Kaggle *Kaggriculture* simulation competition
> (final: rank 401, silver medal, score 2185.6). The final agent is a **rule-based route-replay agent distilled from
> public top-100 replays**, built on Apache-2.0 public notebooks. No neural network or reinforcement learning was used.
> The repository also records what did *not* work, including a large gap between local win rates and the hosted rating.

## 最終エージェント

| 項目 | 内容 |
|---|---|
| 名前 | `rank95_front97` |
| 提出 ID | 56720329（2026-10-01 07:34 JST 提出） |
| 提出直後のスコア | 1057.9 |
| 最終スコア | **2185.6**（401位） |
| 方式 | 公開リプレイ（95位の対戦）の行動ルートを再生し、ルールベースで補正 |
| Kaggle ノートブック | [Kaggriculture 401 Silver rank95 front97](https://www.kaggle.com/code/sol12378/kaggriculture-401-silver-rank95-front97)（Apache 2.0、2026-10-15 公開） |

詳細は [docs/FINAL_AGENT.md](docs/FINAL_AGENT.md) を参照してください。

## 提出した全エージェント

| 日付 (UTC) | 提出 ID | 内容 | 提出直後 | 最終 |
|---|---|---|---:|---:|
| 09-07 | 56067217 | B0 ベースライン | 1288.4 | - |
| 09-21 | 56435924 | D3_MARKET_CAP_V1 | 1074.3 | - |
| 09-22 | 56454639 | Aurax shop v7 公開コピー | 1331.8 | 1331.8 |
| 09-30 | 56692389 | Aurax V7 fallback（無改変） | 1178.1 | 1178.1 |
| 09-30 | 56692403 | ORTHO V4 mask32 | 1296.6 | 1296.6 |
| 09-30 | 56693932 | Top20 リプレイ蒸留（入口関数の不具合） | 149.2 | 149.2 |
| 09-30 | 56702533 | Top20 counter small5 | 1254.4 | 1256.4 |
| 10-01 | 56720329 | **Top100 蒸留 rank95_front97** | 1057.9 | **2185.6** |

「提出直後」は `results/SUBMISSIONS.csv` の記録（Kaggle CLI で読み取った値）です。「最終」は提出ページに表示された値で、
`-` は最終値を記録していません。レーティングは対戦が進むと大きく動くため、提出直後の値は参考になりませんでした。

## リポジトリ構成

```
agents/     提出したエージェント（main.py、LICENSE、NOTICE、提出アーカイブ、検証記録）
  rank95_front97/        最終エージェント
  top20_counter_small5/  Tetsutani V23 を土台にした改良版
  ortho_v4_mask32/       Aurax V7 に1点だけ改造を加えた版
kaggle/     Kaggle に公開したノートブックのソース（.ipynb）とメタデータ
tools/      蒸留・選別・総当たり対戦・パッケージ検証のスクリプト
results/    提出一覧、最終レポート、対戦結果の要約
docs/       時系列、最終エージェントの解説、教訓
```

## 再現について

- リプレイ本体は同梱していません。`tools/top100_replay_distill/` のスクリプトで、認可された Kaggle アカウントから取得できます。
- ローカル評価には `kaggle-environments` 1.32.7 を使いました。
- `results/` の数値は当時の記録で、再実行で同じ値になることは保証しません。

## ライセンスと出典

- `agents/*/main.py` は、Apache-2.0 の公開 Notebook を土台にしています。各ファイルのヘッダー、`NOTICE`、`LICENSE` に出典と帰属を残しています。
  主な出典は thomastschinkel、yhay81、destbreso、aurax7（Yaxon）、tetsutani、prvsiyan、Dmitrii Gluzdov、
  Rayk Kretzschmar、Ahmed Berat Ozer です。
- 行動ルートは、競技中に公開されていた完了済みリプレイに由来します。相手のソースコードや非公開の観測は使っていません。
- このリポジトリ全体は **Apache-2.0** です（[LICENSE](LICENSE)、[NOTICE](NOTICE)）。
  土台にした公開コードがすべて Apache-2.0 であり、コンペのルールが要求する「商用利用を制限しない OSI 承認ライセンス」にも合います。
- 出典の一覧と、再配布の根拠は [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md) にあります。
