# 画像向き自動補正ツール (Image Orientation Auto-Correction Tool)

画像の上下や回転方向を自動判定し、正しい向きに補正する **Windows 向けデスクトップツール**です。

EXIF 情報がない画像にも対応しており、**EXIF 判定・肌色領域検出・画像特徴分析**を組み合わせたハイブリッド方式で向きを推定します。

動画のスナップショット、スマートフォン写真、人物写真など、**上下が逆になった画像**や**回転して保存された画像**の一括補正を想定しています。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

> 推奨 Topics: `python`, `pyside6`, `windows`, `desktop-application`, `image-processing`, `computer-vision`, `image-orientation`, `photo-rotation`, `onnxruntime`, `multilingual`

> 更新履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。

## 特徴

- **3段階ハイブリッド自動向き判定**
  1. EXIF 情報（`Orientation` タグ）— 精度100%・最速
  2. 肌色領域検出（YCrCb変換＋モルフォロジー処理）— 人物写真向け
  3. 画像特徴分析（明るさ／エッジ方向／色分布／テクスチャ）— EXIF がない画像向けのフォールバック
- **顔検出フィルター**
  - BlazeFace (ONNX) で顔を検出し、顔未検出の画像を自動で選択状態にできます
- **手動回転・一括選択**
  - 左90°／右90°／180°の手動回転
  - クリック／Shift+クリック／Ctrl+クリックによる複数選択
- **安全な編集フロー**
  - 編集内容はメモリ上で保持され、「💾 元ファイルに反映する」ボタンを押すまで元ファイルは変更されません
- **多言語対応**
  - 日本語・英語・韓国語・ドイツ語・ロシア語・フランス語・簡体字中国語・繁体字中国語（台湾）の 8 言語に対応
- **Windows 向け GUI**
  - ダーク／ライトテーマ、トースト通知、ズーム対応プレビューダイアログを搭載
- **exe 配布対応**
  - PyInstaller による exe 化を想定しています

## 向いている用途

- 縦画面動画から切り出したスナップショットの向き補正
- スマートフォン写真の一括整理
- 人物写真の上下判定補助
- EXIF 情報が欠落した画像の回転補正
- 手動確認を前提にした安全なバッチ補正ワークフロー

## 動作環境

- Windows 10 / 11
- Python 3.11 以降
- [Anaconda](https://www.anaconda.com/) または pip

## クイックスタート

### Anaconda を使う場合（推奨）

```powershell
git clone https://github.com/yourname/image-orient-tool.git
cd image-orient-tool
conda env create -f environment.yml
conda activate image-orient-tool
python run.py
```

### pip のみの場合

```powershell
git clone https://github.com/yourname/image-orient-tool.git
cd image-orient-tool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## セットアップ

### 顔検出モデルの取得（顔検出フィルターを使う場合のみ・要ネット接続）

```powershell
python download_blazeface.py
```

`image_orient_tool/resources/models/blazeface.onnx` にモデルが保存されます。  
顔検出フィルターを使わない場合、この手順は不要です。

### 翻訳ファイルのビルド（日本語以外の言語を使う場合のみ）

```powershell
python build_translations.py
```

## 使い方

```powershell
python run.py
```

1. 「📁 画像を読み込む」で画像ファイルを選択します（複数選択可）
2. 自動判定された向きがおかしい場合は、サムネイルを選択して手動回転ボタンで補正します
3. 「👤 顔検出を有効にする」を ON にすると、顔が写っていない画像を自動で選択できます
4. 「💾 元ファイルに反映する」を押すと、変更内容が元ファイルに書き込まれます

言語はメニューバー「設定」→「言語 / Language」から切り替えられます。

## 起動前チェック

環境構築後、依存パッケージやファイル構成に問題がないか確認できます。

```powershell
python pre_launch_check.py
```

## テスト

```powershell
python run_all_tests.py
```

## exe 化（PyInstaller）

```powershell
pyinstaller image_orient_tool.spec
```

ビルド後の想定出力:

```text
dist/ImageOrientationTool.exe
```

exe 化する前に `image_orient_tool/resources/icons/appicon.ico` を用意してください。

## 多言語対応

PySide6 公式の Qt Linguist 方式（`tr()` + `.ts` / `.qm` + `QTranslator`）を採用しています。

- `.ts`（翻訳データ）は同梱済みです
- 実行時に必要な `.qm`（バイナリ翻訳ファイル）は `build_translations.py` の実行で生成します

翻訳を修正・追加したい場合は、`image_orient_tool/i18n/app_*.ts` を直接編集するか、`pyside6-linguist` で開いて編集してください。  
編集後は `build_translations.py` を再実行すると反映されます。  
詳しい手順は `image_orient_tool/i18n_support.py` のコメントを参照してください。

## プロジェクト構成

```text
image-orient-tool/
├── run.py                          # エントリポイント
├── download_blazeface.py           # 顔検出モデルのダウンローダ
├── build_translations.py           # 翻訳ファイル (.ts → .qm) のビルドスクリプト
├── check_environment.py            # 環境確認
├── pre_launch_check.py             # 起動前の総合チェック
├── run_all_tests.py                # 全テスト一括実行
├── requirements.txt
├── environment.yml
├── image_orient_tool.spec          # PyInstaller 設定
├── image_orient_tool/
│   ├── app.py                      # QApplication 生成・テーマ／言語適用
│   ├── main_window.py              # MainWindow（UI・ロジックのハブ）
│   ├── settings_manager.py         # QSettings ラッパ
│   ├── i18n_support.py             # 言語判定・QTranslator ロード
│   ├── i18n/                       # 翻訳ファイル (.ts / .qm)
│   ├── core/
│   │   ├── models.py               # ImageItem データクラス
│   │   ├── orientation.py          # 3段階ハイブリッド向き判定
│   │   ├── face_detection.py       # BlazeFace ONNX ラッパ
│   │   └── batch_processor.py      # QThreadPool による並列処理
│   ├── ui/
│   │   ├── preview.py              # プレビューダイアログ（ズーム対応）
│   │   └── toast.py                # トースト通知
│   ├── theme/
│   │   └── palette.py              # ダーク／ライト QPalette
│   ├── util/
│   │   └── paths.py                # PyInstaller 対応のリソースパス解決
│   └── resources/
│       ├── models/                 # blazeface.onnx の配置先
│       └── icons/                  # appicon.ico の配置先
└── tests/
    ├── test_basic_functionality.py
    ├── test_face_detection.py
    └── test_gui_basic.py
```

## 使用ライブラリ・モデル

| 依存 | ライセンス | 用途 |
|---|---|---|
| [PySide6](https://doc.qt.io/qtforpython-6/) | LGPL v3 | GUI フレームワーク |
| [OpenCV](https://opencv.org/) | Apache 2.0 | 画像処理 |
| [Pillow](https://python-pillow.org/) | HPND | EXIF 読み書き |
| [ONNX Runtime](https://onnxruntime.ai/) | MIT | 顔検出モデルの推論 |
| [garavv/blazeface-onnx](https://huggingface.co/garavv/blazeface-onnx) | 要確認 | 顔検出モデル本体 |
| [darkdetect](https://github.com/albertosottile/darkdetect) | BSD-3-Clause | OS のダーク／ライト設定検出 |
| [PyInstaller](https://pyinstaller.org/) | GPL（ブートローダ例外あり） | exe 化 |

## 開発メモ

このツールは、**EXIF がない画像でも自動で向きを推定できること**を重視して設計されています。  
完全自動の一括補正だけでなく、**顔検出フィルターや手動回転を併用できる確認型ワークフロー**を採用しているため、誤判定リスクを抑えながら整理作業を進められます。

## コントリビュート

Issue・Pull Request を歓迎します。  
翻訳の改善、顔検出モデルの改善、向き判定ロジックの精度向上に関する提案も歓迎します。

開発の経緯や設計判断の詳細（PyQt5 → PySide6 移行の理由、i18n 実装の内部仕様など）は [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) を参照してください。

## ライセンス

[MIT License](./LICENSE)

## Copyright

Copyright © 2026 Kirino Subaru