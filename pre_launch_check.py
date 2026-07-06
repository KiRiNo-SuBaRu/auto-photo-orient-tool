# pre_launch_check.py
"""
アプリ起動前の最終チェック
"""
import sys
from pathlib import Path


def print_header(title):
    """ヘッダーを表示"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_files():
    """必要ファイルの存在確認"""
    print_header("ファイル存在確認")
    
    required_files = [
        "run.py",
        "image_orient_tool/__init__.py",
        "image_orient_tool/app.py",
        "image_orient_tool/main_window.py",
        "image_orient_tool/settings_manager.py",
        "image_orient_tool/core/__init__.py",
        "image_orient_tool/core/models.py",
        "image_orient_tool/core/orientation.py",
        "image_orient_tool/core/face_detection.py",
        "image_orient_tool/ui/__init__.py",
        "image_orient_tool/ui/preview.py",
        "image_orient_tool/ui/toast.py",
        "image_orient_tool/theme/__init__.py",
        "image_orient_tool/util/__init__.py",
        "image_orient_tool/util/paths.py",
        "image_orient_tool/resources/models/blazeface.onnx"
    ]
    
    all_ok = True
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            size = ""
            if path.is_file():
                size_bytes = path.stat().st_size
                if size_bytes > 1024 * 1024:
                    size = f"({size_bytes / 1024 / 1024:.1f} MB)"
                elif size_bytes > 1024:
                    size = f"({size_bytes / 1024:.1f} KB)"
                else:
                    size = f"({size_bytes} B)"
            
            print(f"✓ {file_path:60s} {size}")
        else:
            print(f"✗ {file_path:60s} [見つかりません]")
            all_ok = False
    
    return all_ok


def check_imports():
    """インポート確認"""
    print_header("インポート確認")
    
    imports = [
        ("PySide6", "PySide6.QtWidgets"),
        ("OpenCV", "cv2"),
        ("Pillow", "PIL"),
        ("NumPy", "numpy"),
        ("ONNX Runtime", "onnxruntime"),
        ("darkdetect", "darkdetect")
    ]
    
    all_ok = True
    
    for name, module_name in imports:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {name:20s} {version}")
        except ImportError as e:
            print(f"✗ {name:20s} インポートエラー: {e}")
            all_ok = False
    
    return all_ok


def check_app_modules():
    """アプリモジュールのインポート確認"""
    print_header("アプリモジュール確認")
    
    modules = [
        "image_orient_tool.core.models",
        "image_orient_tool.core.orientation",
        "image_orient_tool.core.face_detection",
        "image_orient_tool.ui.preview",
        "image_orient_tool.ui.toast",
        "image_orient_tool.util.paths",
        "image_orient_tool.settings_manager",
        "image_orient_tool.main_window"
    ]
    
    all_ok = True
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}")
            print(f"   エラー: {e}")
            all_ok = False
    
    return all_ok


def check_syntax():
    """構文エラーチェック"""
    print_header("構文エラーチェック")
    
    python_files = list(Path("image_orient_tool").rglob("*.py"))
    python_files.append(Path("run.py"))
    
    all_ok = True
    errors = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            errors.append((py_file, e))
            all_ok = False
    
    if all_ok:
        print(f"✓ {len(python_files)}個のPythonファイルに構文エラーはありません")
    else:
        print(f"✗ {len(errors)}個のファイルに構文エラーがあります:")
        for file, error in errors:
            print(f"  {file}: {error}")
    
    return all_ok


def main():
    """メイン処理"""
    print("=" * 70)
    print("画像向き自動補正ツール v3.3 - 起動前チェック")
    print("=" * 70)
    
    checks = [
        ("ファイル", check_files),
        ("インポート", check_imports),
        ("アプリモジュール", check_app_modules),
        ("構文エラー", check_syntax)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"✗ チェック実行エラー: {e}")
            results[name] = False
    
    # 最終結果
    print_header("最終結果")
    
    all_passed = all(results.values())
    
    for name, result in results.items():
        status = "✓ OK" if result else "✗ NG"
        print(f"{name:20s}: {status}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✓ すべてのチェックに合格しました！")
        print("\n次のコマンドでアプリを起動してください:")
        print("  python run.py")
        print("\nまたは:")
        print("  conda activate image-orient-tool")
        print("  python run.py")
        return 0
    else:
        print("✗ 一部のチェックに失敗しました")
        print("\n以下を確認してください:")
        print("  1. setup_conda.bat/sh を実行")
        print("  2. download_blazeface.py を実行")
        print("  3. エラーメッセージを確認")
        return 1


if __name__ == "__main__":
    sys.exit(main())