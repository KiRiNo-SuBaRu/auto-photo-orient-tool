# download_blazeface.py
"""
BlazeFace ONNXモデルのダウンロードスクリプト
"""
import urllib.request
from pathlib import Path
import sys


def download_blazeface_model(force: bool = False):
    """
    BlazeFace ONNXモデルをダウンロード
    
    Args:
        force: 既存ファイルを上書きするか
    """
    # 保存先ディレクトリ
    model_dir = Path("image_orient_tool/resources/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / "blazeface.onnx"
    
    # 既に存在する場合
    if model_path.exists() and not force:
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ モデルは既に存在します: {model_path}")
        print(f"  サイズ: {size_mb:.2f} MB")
        
        response = input("再ダウンロードしますか? (y/N): ")
        if response.lower() != 'y':
            return
    
    # ダウンロード
    print("\n" + "=" * 60)
    print("BlazeFace ONNXモデルをダウンロード中...")
    print("=" * 60)
    
    # HuggingFace garavv/blazeface-onnx
    # (以前指定していた onnx-community/blazeface は実在しないリポジトリでした)
    url = "https://huggingface.co/garavv/blazeface-onnx/resolve/main/blaze.onnx?download=true"
    
    try:
        # プログレスバー付きダウンロード
        def reporthook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded / total_size * 100, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\r[{bar}] {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='', flush=True)
        
        urllib.request.urlretrieve(url, model_path, reporthook)
        print()  # 改行
        
        # ダウンロード完了
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ ダウンロード完了!")
        print(f"  保存先: {model_path}")
        print(f"  サイズ: {size_mb:.2f} MB")
        
        # 検証
        print("\nモデルファイルを検証中...")
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(str(model_path))
            inputs = session.get_inputs()
            outputs = session.get_outputs()
            
            print("✓ モデルファイルは正常です")
            print(f"  入力: {inputs[0].name} {inputs[0].shape}")
            print(f"  出力数: {len(outputs)}")
            
        except Exception as e:
            print(f"✗ モデルファイルの検証に失敗しました: {e}")
            print("  モデルファイルが破損している可能性があります。")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ ダウンロード失敗: {e}")
        print("\n以下を確認してください:")
        print("  1. インターネット接続")
        print("  2. HuggingFaceへのアクセス制限")
        print("  3. ディスクの空き容量")
        sys.exit(1)


def check_dependencies():
    """依存パッケージの確認"""
    print("依存パッケージを確認中...")
    
    missing = []
    
    try:
        import onnxruntime
        print(f"  ✓ onnxruntime {onnxruntime.__version__}")
    except ImportError:
        missing.append("onnxruntime")
    
    try:
        import cv2
        print(f"  ✓ opencv-python {cv2.__version__}")
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
        print(f"  ✓ numpy {numpy.__version__}")
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print(f"\n✗ 以下のパッケージがインストールされていません:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n以下のコマンドでインストールしてください:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)
    
    print("✓ 全ての依存パッケージが揃っています\n")


if __name__ == "__main__":
    print("=" * 60)
    print("BlazeFace ONNXモデル ダウンロードツール")
    print("=" * 60)
    print()
    
    # 依存関係チェック
    check_dependencies()
    
    # 引数解析
    force = "--force" in sys.argv or "-f" in sys.argv
    
    # ダウンロード実行
    download_blazeface_model(force=force)
    
    print("\n" + "=" * 60)
    print("セットアップ完了!")
    print("=" * 60)
    print("\n次のコマンドでアプリを起動できます:")
    print("  python run.py")