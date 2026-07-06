# packaging/make_release_zip.ps1
#
# pyinstaller でビルド済みの exe と、配布に必要なファイルをまとめて
# リリース用ZIPを作成するスクリプト。
#
# 使い方:
#   .\packaging\make_release_zip.ps1 -Version "4.4.0"
#
# 前提: 事前に以下を実行済みであること
#   python download_blazeface.py
#   python build_translations.py
#   pyinstaller image_orient_tool.spec

param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

$ExeName    = "ImageOrientationTool.exe"
$ExePath    = "dist\$ExeName"
$ZipName    = "ImageOrientationTool-v$Version-win64.zip"
$StageDir   = "dist\release_staging"

if (-not (Test-Path $ExePath)) {
    Write-Error "$ExePath が見つかりません。先に `pyinstaller image_orient_tool.spec` を実行してください。"
    exit 1
}

if (Test-Path $StageDir) {
    Remove-Item $StageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir | Out-Null

Copy-Item $ExePath                          "$StageDir\$ExeName"
Copy-Item "packaging\README_for_release.txt" "$StageDir\README.txt"
Copy-Item "LICENSE"                          "$StageDir\LICENSE.txt"
Copy-Item "CHANGELOG.md"                     "$StageDir\CHANGELOG.txt"

$zipPath = "dist\$ZipName"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path "$StageDir\*" -DestinationPath $zipPath

Remove-Item $StageDir -Recurse -Force

Write-Host "✓ 作成しました: $zipPath"
