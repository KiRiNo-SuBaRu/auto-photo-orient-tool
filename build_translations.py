# build_translations.py
"""
image_orient_tool/i18n/*.ts を .qm にコンパイルするビルドスクリプト

このスクリプトはPySide6が実際にインストールされた環境（このリポジトリの
conda環境 or venv）で実行してください。pyside6-lrelease コマンドを
サブプロセスとして呼び出します。

使い方:
    conda activate image-orient-tool
    python build_translations.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

LANGUAGES = ["en", "ko", "de", "ru", "fr", "zh_CN", "zh_TW"]
I18N_DIR = Path("image_orient_tool/i18n")


def find_lrelease() -> str:
    """pyside6-lrelease コマンドの実体を探す"""
    exe = shutil.which("pyside6-lrelease")
    if exe:
        return exe
    # Windowsで PATH に無い場合、Pythonと同じ場所のScriptsを探す
    candidate = Path(sys.executable).parent / "pyside6-lrelease.exe"
    if candidate.exists():
        return str(candidate)
    candidate = Path(sys.executable).parent / "Scripts" / "pyside6-lrelease.exe"
    if candidate.exists():
        return str(candidate)
    raise FileNotFoundError(
        "pyside6-lrelease が見つかりません。PySide6 が正しくインストールされているか確認してください。\n"
        "  pip install PySide6  または  conda install -c conda-forge pyside6"
    )


def main():
    lrelease = find_lrelease()
    print(f"✓ pyside6-lrelease: {lrelease}")

    if not I18N_DIR.exists():
        print(f"✗ {I18N_DIR} が見つかりません。")
        sys.exit(1)

    ok, failed = 0, 0
    for lang in LANGUAGES:
        ts_path = I18N_DIR / f"app_{lang}.ts"
        qm_path = I18N_DIR / f"app_{lang}.qm"

        if not ts_path.exists():
            print(f"⚠ スキップ（.tsが見つかりません）: {ts_path}")
            continue

        result = subprocess.run(
            [lrelease, str(ts_path), "-qm", str(qm_path)],
            capture_output=True, text=True
        )

        if result.returncode == 0 and qm_path.exists():
            print(f"✓ {ts_path.name} -> {qm_path.name} ({qm_path.stat().st_size} bytes)")
            ok += 1
        else:
            print(f"✗ 失敗: {ts_path.name}")
            print(result.stdout)
            print(result.stderr)
            failed += 1

    print(f"\n完了: 成功 {ok} / 失敗 {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
