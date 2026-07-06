# 画像向き自動補正ツール (Image Orientation Auto-Correction Tool)

縦画面で撮影された動画のスナップショット群を、**上下を自動判別して正しい向きに回転**させる
Windows向けデスクトップツールです。EXIF情報がない画像でも、肌色検出や画像特徴分析を使った
ハイブリッド判定で向きを推定します。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

> 更新履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。

## 主な機能

- **3段階ハイブリッド自動向き判定**
  1. EXIF情報（`Orientation`タグ）— 精度100%・最速
  2. 肌色領域検出（YCrCb変換＋モルフォロジー処理）— 人物写真向け
  3. 画像特徴分析（明るさ／エッジ方向／色分布／テクスチャ）— フォールバック
- **顔検出フィルター**: BlazeFace(ONNX)で顔を検出し、顔未検出の画像を自動で選択状態に
- **手動回転・一括選択**: 左90°／右90°／180°の手動回転、クリック／Shift+クリック／
  Ctrl+クリックによる複数選択
- **安全な編集フロー**: メモリ上で編集し、「💾 元ファイルに反映する」ボタンを押すまで
  元ファイルは変更されません
- **多言語対応**: 日本語・英語・韓国語・ドイツ語・ロシア語・フランス語・簡体字中国語・
  繁体字中国語（台湾）の8言語（詳細は [多言語対応](#多言語対応) を参照）
- ダーク／ライトテーマ、トースト通知、ズーム対応プレビューダイアログ
- PyInstallerによるexe化に対応

## 動作環境

- Windows 10 / 11
- Python 3.11 以降
- [Anaconda](https://www.anaconda.com/) または pip

## インストール

### Anaconda を使う場合（推奨）

```powershell
git clone https://github.com/yourname/image-orient-tool.git
cd image-orient-tool
conda env create -f environment.yml
conda activate image-orient-tool
```

### pip のみの場合

```powershell
git clone https://github.com/yourname/image-orient-tool.git
cd image-orient-tool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

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

1. 「📁 画像を読み込む」で画像ファイルを選択（複数選択可）
2. 自動判定された向きがおかしい場合はサムネイルを選択し、手動回転ボタンで補正
3. 「👤 顔検出を有効にする」をONにすると、顔が写っていない画像を自動で選択
4. 「💾 元ファイルに反映する」を押すと、変更が元ファイルに書き込まれます

言語はメニューバー「設定」→「言語 / Language」から切り替えられます。

## 起動前チェック（任意）

環境構築後、依存パッケージやファイル構成に問題がないか確認できます。

```powershell
python pre_launch_check.py
```

## テスト

```powershell
python run_all_tests.py
```

## exe化（PyInstaller）

```powershell
pyinstaller image_orient_tool.spec
# → dist/ImageOrientationTool.exe
```

アイコン（`image_orient_tool/resources/icons/appicon.ico`）は同梱済みです。
差し替えたい場合はファイルを置き換えてください。

## 多言語対応

PySide6公式のQt Linguist方式（`tr()` + `.ts`/`.qm` + `QTranslator`）を採用しています。
`.ts`（翻訳データ）は同梱済みですが、実行時に読み込む`.qm`（バイナリ）は
`build_translations.py` の実行で生成する必要があります。

翻訳を修正・追加したい場合は、`image_orient_tool/i18n/app_*.ts` を直接編集するか、
`pyside6-linguist` で開いて編集してください。編集後は `build_translations.py` の
再実行で反映されます。詳しい手順はコード内コメント（`image_orient_tool/i18n_support.py`）
を参照してください。

## プロジェクト構成

```
image-orient-tool/
├── run.py                          # エントリポイント
├── download_blazeface.py           # 顔検出モデルのダウンローダ
├── build_translations.py           # 翻訳ファイル(.ts→.qm)のビルドスクリプト
├── check_environment.py            # 環境確認
├── pre_launch_check.py             # 起動前の総合チェック
├── run_all_tests.py                # 全テスト一括実行
├── requirements.txt / environment.yml
├── image_orient_tool.spec          # PyInstaller設定
├── image_orient_tool/
│   ├── app.py                      # QApplication生成・テーマ／言語適用
│   ├── main_window.py              # MainWindow（UI・ロジックのハブ）
│   ├── settings_manager.py         # QSettingsラッパ
│   ├── i18n_support.py             # 言語判定・QTranslatorロード
│   ├── i18n/                       # 翻訳ファイル(.ts/.qm)
│   ├── core/
│   │   ├── models.py               # ImageItem データクラス
│   │   ├── orientation.py          # 3段階ハイブリッド向き判定
│   │   ├── face_detection.py       # BlazeFace ONNXラッパ
│   │   └── batch_processor.py      # QThreadPoolによる並列処理
│   ├── ui/
│   │   ├── preview.py               # プレビューダイアログ（ズーム対応）
│   │   └── toast.py                # トースト通知
│   ├── theme/
│   │   └── palette.py              # ダーク/ライトQPalette
│   ├── util/
│   │   └── paths.py                # PyInstaller対応のリソースパス解決
│   └── resources/
│       ├── models/                 # blazeface.onnx の配置先
│       └── icons/                  # appicon.ico(同梱済み)
└── tests/
    ├── test_basic_functionality.py
    ├── test_face_detection.py
    └── test_gui_basic.py
```

## 使用ライブラリ・モデル

| 依存 | ライセンス | 用途 |
|---|---|---|
| [PySide6](https://doc.qt.io/qtforpython-6/) | LGPL v3 | GUIフレームワーク |
| [OpenCV](https://opencv.org/) | Apache 2.0 | 画像処理 |
| [Pillow](https://python-pillow.org/) | HPND | EXIF読み書き |
| [ONNX Runtime](https://onnxruntime.ai/) | MIT | 顔検出モデルの推論 |
| [garavv/blazeface-onnx](https://huggingface.co/garavv/blazeface-onnx) | 要確認 | 顔検出モデル本体 |
| [darkdetect](https://github.com/albertosottile/darkdetect) | BSD-3-Clause | OSのダーク/ライト設定検出 |
| [PyInstaller](https://pyinstaller.org/) | GPL（ブートローダ例外あり） | exe化 |

## コントリビュート

Issue・Pull Requestを歓迎します。翻訳の改善（特にAI翻訳のネイティブチェック）も
大歓迎です。

開発の経緯や設計判断の詳細（PyQt5→PySide6移行の理由、i18n実装の内部仕様など）は
[docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) を参照してください。

## ライセンス

[MIT License](./LICENSE)
