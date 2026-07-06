# 更新履歴 (Changelog)

このプロジェクトの変更履歴です。[Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)
の形式に準拠し、[Semantic Versioning](https://semver.org/lang/ja/) を採用しています。

## [Unreleased]

- （現時点で未リリースの変更はありません）

## [4.4.0] - 2026-07-06

### Added

- `image_orient_tool/resources/icons/appicon.ico` を作成・同梱。
  「傾いた人物写真＋回転矢印」のデザイン（16/24/32pxはシンプル版、48px以上は
  人物シルエット入り詳細版を個別に描画し1つの.icoにまとめている）
  - 対応解像度: 16, 24, 32, 48, 72, 96, 128, 256 px
  - これにより `pyinstaller image_orient_tool.spec` でのexe化時に
    別途アイコンを用意する手間がなくなった

## [4.3.0] - 2026-07-06

### Fixed

- 縦横比モード（縦長限定/横長限定）の画像読み込み時の強制回転ロジックを検証し、
  正しく機能していることを確認
- 縦長限定/横長限定モード中に手動で90°回転すると、読み込み時に揃えた縦横比が
  崩れてしまう問題を修正。該当モード中は90°回転ボタンを無効化し、180°回転のみ
  許可するよう変更（`on_rotate_selected()`側にもガードを追加し、二重に防止）

### Added

- `tests/test_gui_basic.py` に縦横比モードの回転ロジック・90°回転制限に関する
  テストを追加
- 上記変更に伴う新規UI文字列（ツールチップ・トースト通知）を7言語分翻訳して追加

## [4.2.0] - 2026-07-06

### Added

- 多言語対応に簡体字中国語(`zh_CN`)・繁体字中国語/台湾(`zh_TW`)を追加（対応言語は計7言語に）
- 中国語の地域判定ロジックを追加（`zh_HK`/`zh_MO`→繁体字、`zh_SG`→簡体字として自動判定）

## [4.1.0] - 2026-07-06

### Added

- 多言語対応（i18n）を実装。日本語（ソース言語）に加えて英語・韓国語・ドイツ語・
  ロシア語・フランス語に対応
- PySide6公式のQt Linguist方式（`tr()` + `.ts`/`.qm` + `QTranslator`）を採用
- メニューバーに「設定」→「言語 / Language」を追加し、アプリ内から言語切替が可能に
  （OSの言語設定への自動追従、または手動選択）
- `build_translations.py`（`.ts`→`.qm`のビルドスクリプト）、`generate_ts_files.py`
  （翻訳データから`.ts`を生成する開発用スクリプト）を追加

### Changed

- `main_window.py` / `ui/preview.py` の全UI文字列（79件）を`tr()`でラップ
- `ImageItem.method` の表示名を翻訳するため `MainWindow._method_display_name()` を追加
  （内部データ値と表示文字列を分離）

## [4.0.0] - 2026-07-06

### Changed

- **GUIフレームワークを PyQt5 から PySide6 に移行**（破壊的変更）
  - ライセンス上の理由（PyQt5のGPL版を使うと配布物全体をGPL互換ライセンスにする必要がある）から、
    LGPL v3で配布されるPySide6に切り替え
  - `pyqtSignal` → `Signal`、`.exec_()` → `.exec()` など、PySide6/Qt6 API差分に追随
  - `environment.yml` / `requirements.txt` の依存パッケージを更新
  - `image_orient_tool.spec`（PyInstaller設定）の `hiddenimports` に `shiboken6` を追加

## [3.3.1] - 2026-07-03

### Fixed

- `download_blazeface.py` が参照していたモデルURL（`onnx-community/blazeface`）が
  実在しないリポジトリで `HTTP Error 401: Unauthorized` になる不具合を修正。
  実在する [`garavv/blazeface-onnx`](https://huggingface.co/garavv/blazeface-onnx) に差し替え
- 上記モデル差し替えに伴い `core/face_detection.py` の前処理・後処理をこのモデル専用に書き換え
  （`conf_threshold` / `max_detections` / `iou_threshold` を追加入力する仕様に対応）
- onnxruntimeが出力する無害な形状警告（モデルのONNXグラフの出力形状メタデータ不整合による
  warning）を `log_severity_level` 設定で抑制

## [3.3.0] - 2026-07-01

### Added

- 初回リリース。以前の開発ログ（Perplexityスレッド）から実コードを復元し、
  動くプロジェクト一式として再構成
- 3段階ハイブリッド自動向き判定（EXIF → 肌色検出 → 画像特徴分析）
- BlazeFace(ONNX)による顔検出フィルター（顔未検出画像を自動選択）
- 手動回転（左90°／右90°／180°）、複数選択（クリック／Shift/Ctrl+クリック）
- 「元ファイルに反映する」ボタンによる明示的な保存フロー（それまでは元ファイル無傷）
- ダーク／ライトテーマ、トースト通知、ズーム対応プレビューダイアログ
- PyInstallerによるexe化対応（`image_orient_tool.spec`）
- 復元時に不足していた `core/models.py` / `util/paths.py` / `theme/palette.py` を新規実装

[Unreleased]: https://github.com/yourname/image-orient-tool/compare/v4.4.0...HEAD
[4.4.0]: https://github.com/yourname/image-orient-tool/compare/v4.3.0...v4.4.0
[4.3.0]: https://github.com/yourname/image-orient-tool/compare/v4.2.0...v4.3.0
[4.2.0]: https://github.com/yourname/image-orient-tool/compare/v4.1.0...v4.2.0
[4.1.0]: https://github.com/yourname/image-orient-tool/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/yourname/image-orient-tool/compare/v3.3.1...v4.0.0
[3.3.1]: https://github.com/yourname/image-orient-tool/compare/v3.3.0...v3.3.1
[3.3.0]: https://github.com/yourname/image-orient-tool/releases/tag/v3.3.0
