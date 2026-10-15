# 出典と再配布の根拠

このリポジトリの `agents/` は、Apache-2.0 の公開 Kaggle Notebook を土台にしています。
各エージェントの `NOTICE` と `main.py` ヘッダーに、元の著作者表示とライセンス文を残しています。変更点は `NOTICE` に書いています。

## コード（Apache-2.0）

| エージェント | 土台にした公開コード | 出典・備考 |
|---|---|---|
| `ortho_v4_mask32` | Aurax V7（作者 Yaxon） | https://www.kaggle.com/code/aurax7/kaggriculture-shop-router-reactive-v7 。親のバイト列は無改変で埋め込み、PASS を HARVEST に置き換える変更だけを加えています |
| `top20_counter_small5` | Market-Smart Farming（作者 tetsutani） | https://www.kaggle.com/code/tetsutani/market-smart-farming-kaggriculture 。その上に、リプレイに基づく局所補正、ミラー初手の小麦数量ガード、小口売却の順序修正を追加しています |
| `rank95_front97` | 上記の系譜の公開コード | `main.py` ヘッダーに、thomastschinkel、yhay81、destbreso、aurax7、tetsutani、prvsiyan、Dmitrii Gluzdov、Rayk Kretzschmar、Ahmed Berat Ozer の帰属を記載しています |

Aurax V7 と Market-Smart Farming の2本は、2026-10-15 に Kaggle の公開ページで、ライセンスが Apache 2.0 と表示されていることを確認しました。
`rank95_front97` の系譜にある他のノートブックは、`main.py` ヘッダーの Apache-2.0 表記に基づいています（個別のページ確認は未実施）。

## 公開リプレイ由来の行動ルート

- `rank95_front97` の基本ルートは、競技中に公開されていた完了済みリプレイ（95位の対戦 `115755103`）の行動列です。97位の別の開発用リプレイの売却予定も参照しています。
- 競技ルールには「各エピソードのリプレイは、公開・ダウンロードできる場合がある」と書かれています。
  リプレイ本体（観測を含む全体）は同梱せず、**エージェント自身の行動列だけ**を埋め込んでいます。
- 公開 Notebook にも、同じ方法（公開リプレイの行動列を Apache-2.0 で公開）のものがあり、ヘッダーで出典として挙げられています。
- 相手のソースコード、非公開の観測、モデルの重みは使っていません。
- 権利者から削除の要望があれば、該当部分を取り除きます。

## 競技環境

- ローカル評価に `kaggle-environments`（Apache-2.0）を使いました。このリポジトリには含めていません。
- コンペの Data ページは、データのライセンスを Apache 2.0 と表示しています（Python キットのみ）。リプレイはこのデータに含まれません。
