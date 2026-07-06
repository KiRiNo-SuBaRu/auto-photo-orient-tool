# image_orient_tool/util/paths.py
"""
リソースファイルへのパス解決ヘルパー
開発時（スクリプト実行）とPyInstallerでexe化された後の両方で
resources/ 以下のファイルを正しく見つけられるようにする。
"""
import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """
    リソースファイルへの絶対パスを返す

    Args:
        relative_path: "resources/models/blazeface.onnx" のような
                        image_orient_tool パッケージ内からの相対パス

    Returns:
        実行環境に応じた絶対パス
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstallerでexe化された場合、一時展開ディレクトリを使う
        base_path = Path(sys._MEIPASS)
    else:
        # 開発時: image_orient_tool パッケージのルートを基準にする
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path
