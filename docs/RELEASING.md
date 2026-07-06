# リリース手順 (RELEASING.md)

exeビルドからGitHub公開までの一連の手順をまとめたものです。

## 1. ビルド前の準備

```powershell
conda activate image-orient-tool
python download_blazeface.py       # 顔検出モデルを取得(初回のみ)
python build_translations.py       # .ts -> .qm をビルド
python run_all_tests.py            # テストが全て通ることを確認
```

## 2. exeをビルド

```powershell
pyinstaller image_orient_tool.spec
```

`dist\ImageOrientationTool.exe` が生成されます
（`image_orient_tool.spec` の `datas` 設定により、顔検出モデルと翻訳ファイルは
自動的にexeに同梱されます。ユーザー側で追加のダウンロード作業は不要です）。

## 3. 配布用ZIPを作成

`packaging/make_release_zip.ps1` が、exe・エンドユーザー向けReadme・
LICENSE・CHANGELOGをまとめてZIP化します。

```powershell
.\packaging\make_release_zip.ps1 -Version "4.4.0"
```

`dist\ImageOrientationTool-v4.4.0-win64.zip` が生成されます。

手動でやる場合は以下と同じ内容です。

1. 新しいフォルダ（例: `release`）を作る
2. `dist\ImageOrientationTool.exe` をコピー
3. `packaging\README_for_release.txt` を `README.txt` としてコピー
4. `LICENSE` を `LICENSE.txt` としてコピー
5. `CHANGELOG.md` を `CHANGELOG.txt` としてコピー
6. フォルダごとZIP圧縮（フォルダ名: `ImageOrientationTool-v4.4.0-win64.zip`）

## 4. ソースコードをGitHubにpush

初めて公開する場合:

```powershell
git init
git add .
git commit -m "Initial commit: v4.4.0"
git branch -M main
git remote add origin https://github.com/yourname/image-orient-tool.git
git push -u origin main
```

既存リポジトリに変更を反映する場合:

```powershell
git add .
git commit -m "Release v4.4.0"
git push
```

`.gitignore` に以下を入れておくと、ビルド成果物や一時ファイルが
誤ってコミットされるのを防げます（未作成の場合は追加してください）。

```
__pycache__/
*.pyc
build/
dist/
*.qm
image_orient_tool/resources/models/*.onnx
.venv/
```

（`.qm`と`.onnx`は容量が大きく・ビルドで再生成できるためリポジトリには含めない運用を推奨。
ソースを取得した人は `build_translations.py` / `download_blazeface.py` を
実行すれば同じものが手元で生成できます）

## 5. バージョンにタグを付ける

```powershell
git tag -a v4.4.0 -m "v4.4.0"
git push origin v4.4.0
```

## 6. GitHub Releaseを作成し、ZIPを添付

### Web UIから行う場合

1. GitHubリポジトリページ → 右側 "Releases" → "Draft a new release"
2. "Choose a tag" で `v4.4.0` を選択（手順5でpush済みのタグ）
3. タイトルに `v4.4.0` などバージョンを入力
4. 本文に `CHANGELOG.md` の該当バージョンの内容を貼り付け
5. "Attach binaries" 欄に手順3で作った
   `ImageOrientationTool-v4.4.0-win64.zip` をドラッグ＆ドロップ
6. "Publish release" をクリック

### GitHub CLI (`gh`) を使う場合

```powershell
gh release create v4.4.0 `
    "dist\ImageOrientationTool-v4.4.0-win64.zip" `
    --title "v4.4.0" `
    --notes-file CHANGELOG.md
```

（`gh` 未インストールの場合は https://cli.github.com/ から導入するか、
Web UIの手順を使ってください）

## 7. 公開後の確認

- Releaseページからzipをダウンロードし、別のWindows PC（または同一PCの別フォルダ）で
  実際に解凍・起動して動作することを確認する
- リポジトリの `README.md` のダウンロードリンク（Releasesページへのリンク）が
  正しいバージョンを指しているか確認する

## リリースのたびに繰り返す作業まとめ

1. `CHANGELOG.md` に新バージョンのエントリを追記
2. 手順1〜3（テスト→ビルド→ZIP化）
3. `git commit` → `git push`
4. `git tag` → `git push origin <tag>`
5. GitHub Releaseを作成しZIPを添付
