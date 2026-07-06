# 開発者向け技術メモ

このドキュメントは、一般ユーザー向けの [README.md](../README.md) には含めていない、
開発の経緯や設計判断の詳細をまとめたものです。

## PyQt5 → PySide6 移行について（v4.0.0）

このプロジェクトはもともとPyQt5(GPL v3)で実装されていましたが、ライセンス上の理由
（PyQt5のGPL版を使うと配布物全体をGPL互換ライセンスにする必要がある）から
**PySide6（Qtが公式に提供するPythonバインディング、LGPL v3）** に移行しました。

移行に伴う変更点：

- 全ファイルの `from PyQt5.xxx import ...` → `from PySide6.xxx import ...`
- `pyqtSignal` → `Signal`（`main_window.py`, `core/batch_processor.py`）
- `.exec_()` → `.exec()`（`run.py`, `main_window.py`。PySide6では非推奨APIのため必須）
- `environment.yml` / `requirements.txt` の `PyQt5` → `PySide6`
- `image_orient_tool.spec` の `hiddenimports` に `shiboken6` を追加

`QAction` / `QShortcut` / `QDesktopWidget` / `QRegExp` など、Qt5→Qt6でモジュールや
APIが変わったクラスは本プロジェクトでは未使用だったため、上記以外の変更は不要でした。

PySide6はLGPL v3のため、自分のアプリケーションのソースコードを公開する義務はありません
（PySide6自体に変更を加えて配布する場合のみ、その変更差分の公開が必要です）。
そのため本リポジトリのライセンスはGPL v3に縛られず、MIT・Apache 2.0など自由に選べます
（本リポジトリではMITを採用）。

## 多言語対応（i18n）の実装詳細（v4.1.0 / v4.2.0）

- ソース言語（`tr()`に直接書かれている文字列）は日本語です。翻訳先は英・韓・独・露・仏・
  簡体字中国語・繁体字中国語(台湾)の7言語。
- 中国語は簡体字(`zh_CN`)と繁体字(`zh_TW`)で文字体系そのものが異なるため、
  他言語のような2文字コードではなく、ロケール全体をコードとして扱っています。
  OS言語への自動追従時は `zh_CN`/`zh_SG`→簡体字、`zh_TW`/`zh_HK`/`zh_MO`→繁体字（台湾表記）
  にマッピングしています。
- `ImageItem.method`（向き判定方法: `"EXIF"` / `"肌色検出"` など）は内部識別子としてそのまま
  日本語で保持し、表示時のみ `MainWindow._method_display_name()` で翻訳しています。
  内部データと表示文字列を分離することで、将来的な言語追加やロジック変更の影響を避けています。
- 言語切替は即時反映（`retranslateUi`）ではなく、**アプリ再起動方式**を採用しています。
  ウィジェットの動的な再翻訳よりも実装・保守コストが低く、小規模なツールには十分な方式です。
- `generate_ts_files.py` は翻訳データ（Pythonの辞書）から `.ts` を生成する開発用スクリプトです。
  通常の開発フローでは `pyside6-lupdate` を使いますが、本プロジェクトの翻訳データは
  復元・作成時に一括で用意したため、専用スクリプトで生成しています。新規文字列を追加する際は
  `pyside6-lupdate` で追記していく運用に切り替えて問題ありません。

## BlazeFace顔検出モデルの修正経緯（v3.3.1）

以前の開発ログの `download_blazeface.py` が参照していたモデルURL
（`onnx-community/blazeface`）は**実在しないリポジトリ**で、実行すると
`HTTP Error 401: Unauthorized` になります。実際に動作確認できた
[`garavv/blazeface-onnx`](https://huggingface.co/garavv/blazeface-onnx) の
`blaze.onnx` に差し替えました。

このモデルは通常のBlazeFaceと異なり、`image` に加えて `conf_threshold` /
`max_detections` / `iou_threshold` の3つの追加入力を取り、内部でNMS（重複除去）まで
済ませた検出結果（16次元: バウンディングボックス4＋顔ランドマーク6組）を返す
"オールインワン"型のモデルです。`core/face_detection.py` はこのモデル専用の
前処理・後処理に書き換えてあります。

また、このモデルのONNXグラフに埋め込まれた出力形状メタデータが実際の出力と
食い違っているため、onnxruntimeが無害な形状警告(W)を出すことがありますが、
`log_severity_level = 3` を設定して抑制しています。

## プロジェクト復元の経緯（v3.3.0）

本プロジェクトは、以前のPerplexity開発スレッドのログ（HTMLエクスポート）から
実コードを抽出・復元したものです。復元時、以下の3ファイルはログ中で設計仕様として
言及されるのみで完全なコードが提示されていなかったため、既存コードの参照箇所
（import文・使い方）に整合するよう新規に実装しました。

- `core/models.py`（`ImageItem` データクラス）
- `util/paths.py`（`resource_path`、PyInstaller対応のリソースパス解決）
- `theme/palette.py`（ダーク/ライトQPalette）

それ以外のファイルは、ログに含まれていた完全なコードをそのまま復元しています。
