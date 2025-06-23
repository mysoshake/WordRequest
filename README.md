# WordRequest
単語宛てゲーム

## 概要
Word2Vecを使って、ランダムに選ばれた単語を当てるゲームです。
一度質問した単語は一致度のランキングに残り、高いものと低いものがいくつか表示されます。時間内に単語を当てることが出来たらクリアです。
（かなり鬼畜なゲームです）



# 準備
## 1.Gitリポジトリのクローン
次のコマンドを自分の好きなフォルダで実行してください。
``` 
git clone https://github.com/mysoshake/WordRequest.git
```

## 2.Pythonとパッケージ設定
自身の環境にnumpyとgensimとcustomtkinterを入れてください。
``` [requirements]
pip install customtkinter
pip install gensim
pip install numpy
```

## 3.モデルのダウンロード
次のいずれかのWord2Vecのモデルデータをダウンロードしてmodelフォルダに配置してください。モデルによって対応している単語やベクトルが違うので異なる動作で遊べます。

### (A) fastText
- ダウンロードページ: https://fasttext.cc/docs/en/crawl-vectors.html
- モデルのダウンロード
- 日本語のcc.ja.300.vecファイルをmodelフォルダに配置

### (B) Wikipedia Entity Vectors
- リポジトリ: https://github.com/singletongue/WikiEntVec
- ダウンロードページ: https://github.com/singletongue/WikiEntVec/releases
- jawiki.entity_vectors.300d.txt.bz2をダウンロード・展開してjawiki.entity_vectors.300d.txtをmodelフォルダに配置

## 4. 実行
コマンドラインなどから gui_main.py を実行する。
ゲームウィンドウが開くはずです。
