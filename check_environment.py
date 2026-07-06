# check_environment.py - Conda環境の確認スクリプト
"""
Conda環境が正しくセットアップされているか確認するスクリプト
"""
import sys
from pathlib import Path


def check_python_version():
    """Pythonバージョンの確認"""
    print("=" * 60)
    print("Python環境")
    print("=" * 60)
    print(f"バージョン: {sys.version}")
    print(f"実行パス: {sys.executable}")
    
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 10:
        print("✓ Pythonバージョン: OK")
        return True
    else:
        print(f"✗ Pythonバージョン: NG (3.10以上が必要)")
        return False


def check_packages():
    """必須パッケージの確認"""
    print("\n" + "=" * 60)
    print("必須パッケージ")
    print("=" * 60)
    
    packages = {
        'PySide6': 'PySide6',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'numpy': 'numpy',
        'onnxruntime': 'onnxruntime',
        'darkdetect': 'darkdetect'
    }
    
    all_ok = True
    
    for import_name, package_name in packages.items():
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package_name:20s} {version}")
        except ImportError:
            print(f"✗ {package_name:20s} インストールされていません")
            all_ok = False
    
    return all_ok


def check_model_file():
    """BlazeFaceモデルファイルの確認"""
    print("\n" + "=" * 60)
    print("BlazeFaceモデル")
    print("=" * 60)
    
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ モデルファイル: {model_path}")
        print(f"  サイズ: {size_mb:.2f} MB")
        return True
    else:
        print(f"✗ モデルファイルが見つかりません: {model_path}")
        print("  download_blazeface.py を実行してください")
        return False


def check_directory_structure():
    """ディレクトリ構造の確認"""
    print("\n" + "=" * 60)
    print("ディレクトリ構造")
    print("=" * 60)
    
    required_dirs = [
        "image_orient_tool",
        "image_orient_tool/core",
        "image_orient_tool/ui",
        "image_orient_tool/theme",
        "image_orient_tool/util",
        "image_orient_tool/resources/models"
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} が見つかりません")
            all_ok = False
    
    return all_ok


def check_conda_environment():
    """Conda環境の確認"""
    print("\n" + "=" * 60)
    print("Conda環境")
    print("=" * 60)
    
    conda_prefix = Path(sys.prefix)
    env_name = conda_prefix.name
    
    print(f"環境名: {env_name}")
    print(f"環境パス: {conda_prefix}")
    
    if "image-orient-tool" in env_name.lower():
        print("✓ 正しいConda環境で実行されています")
        return True
    else:
        print("⚠ 警告: image-orient-tool環境ではない可能性があります")
        print("  conda activate image-orient-tool を実行してください")
        return False


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("画像向き自動補正ツール v3.3 - 環境確認")
    print("=" * 60)
    print()
    
    results = []
    
    # 各項目をチェック
    results.append(("Pythonバージョン", check_python_version()))
    results.append(("必須パッケージ", check_packages()))
    results.append(("BlazeFaceモデル", check_model_file()))
    results.append(("ディレクトリ構造", check_directory_structure()))
    results.append(("Conda環境", check_conda_environment()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("確認結果サマリー")
    print("=" * 60)
    
    all_ok = True
    for name, result in results:
        status = "✓ OK" if result else "✗ NG"
        print(f"{name:20s}: {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ すべてのチェックに合格しました！")
        print("  python run.py でアプリを起動できます")
    else:
        print("✗ 一部のチェックに失敗しました")
        print("  setup_conda.bat (Windows) または")
        print("  setup_conda.sh (macOS/Linux) を実行してください")
    print("=" * 60)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())