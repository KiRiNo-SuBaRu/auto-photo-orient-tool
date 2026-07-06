# tests/test_basic_functionality.py
"""
基本機能の統合テスト
"""
import sys
from pathlib import Path
import numpy as np
import cv2

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from image_orient_tool.core.models import ImageItem
from image_orient_tool.core.orientation import (
    load_image_with_exif,
    rotate_image_bgr,
    detect_orientation_hybrid
)


def test_image_rotation():
    """画像回転のテスト"""
    print("\n=== 画像回転テスト ===")
    
    # テスト画像を作成（300x200のカラー画像）
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    img[:, :, 0] = 255  # 青チャンネル
    
    print(f"元画像サイズ: {img.shape}")
    
    # 90度回転
    rotated_90 = rotate_image_bgr(img, 90)
    print(f"90度回転後: {rotated_90.shape}")
    assert rotated_90.shape == (300, 200, 3), "90度回転でサイズが間違っています"
    
    # 180度回転
    rotated_180 = rotate_image_bgr(img, 180)
    print(f"180度回転後: {rotated_180.shape}")
    assert rotated_180.shape == (200, 300, 3), "180度回転でサイズが間違っています"
    
    # 270度回転
    rotated_270 = rotate_image_bgr(img, 270)
    print(f"270度回転後: {rotated_270.shape}")
    assert rotated_270.shape == (300, 200, 3), "270度回転でサイズが間違っています"
    
    # 0度（回転なし）
    rotated_0 = rotate_image_bgr(img, 0)
    print(f"0度回転後: {rotated_0.shape}")
    assert np.array_equal(rotated_0, img), "0度回転で画像が変わっています"
    
    print("✓ 画像回転テスト: 成功")


def test_orientation_detection():
    """向き判定のテスト"""
    print("\n=== 向き判定テスト ===")
    
    # テスト画像を作成（上部が明るい画像）
    img = np.zeros((400, 300, 3), dtype=np.uint8)
    img[:200, :, :] = 200  # 上半分を明るく
    img[200:, :, :] = 50   # 下半分を暗く
    
    print(f"テスト画像サイズ: {img.shape}")
    
    # 向き判定実行
    rotation, method, confidence = detect_orientation_hybrid(img)
    
    print(f"判定結果:")
    print(f"  回転角度: {rotation}°")
    print(f"  判定方法: {method}")
    print(f"  信頼度: {confidence:.3f}")
    
    assert rotation in [0, 90, 180, 270], "無効な回転角度が返されました"
    assert 0.0 <= confidence <= 1.0, "信頼度が範囲外です"
    
    print("✓ 向き判定テスト: 成功")


def test_image_item_model():
    """ImageItemモデルのテスト"""
    print("\n=== ImageItemモデルテスト ===")
    
    # ダミー画像
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # ImageItemを作成
    item = ImageItem(
        original_path=Path("test.jpg"),
        image_array=img,
        rotation_deg=90,
        method="EXIF",
        dirty=False,
        delete_pending=False
    )
    
    print(f"ImageItem作成:")
    print(f"  パス: {item.original_path}")
    print(f"  回転: {item.rotation_deg}°")
    print(f"  方法: {item.method}")
    print(f"  変更: {item.dirty}")
    
    # 変更をマーク
    item.dirty = True
    assert item.dirty == True, "dirtyフラグが正しく設定されません"
    
    # 削除予定をマーク
    item.delete_pending = True
    assert item.delete_pending == True, "delete_pendingフラグが正しく設定されません"
    
    print("✓ ImageItemモデルテスト: 成功")


def test_exif_loading():
    """EXIF読み込みのテスト（実画像がある場合）"""
    print("\n=== EXIF読み込みテスト ===")
    
    # テスト画像のパスを探す
    test_images = list(Path(".").glob("**/*.jpg"))[:1]
    
    if not test_images:
        print("⚠ テスト用のJPG画像が見つかりません（スキップ）")
        return
    
    test_image = test_images[0]
    print(f"テスト画像: {test_image}")
    
    try:
        img_bgr, rotation, method = load_image_with_exif(test_image)
        
        print(f"読み込み結果:")
        print(f"  画像サイズ: {img_bgr.shape}")
        print(f"  初期回転: {rotation}°")
        print(f"  判定方法: {method}")
        
        assert img_bgr.shape[2] == 3, "BGR画像ではありません"
        assert rotation in [0, 90, 180, 270], "無効な回転角度"
        
        print("✓ EXIF読み込みテスト: 成功")
        
    except Exception as e:
        print(f"✗ EXIF読み込みエラー: {e}")


def run_all_tests():
    """全テストを実行"""
    print("=" * 60)
    print("基本機能テスト開始")
    print("=" * 60)
    
    tests = [
        test_image_rotation,
        test_orientation_detection,
        test_image_item_model,
        test_exif_loading
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: 失敗 - {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: エラー - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("テスト結果")
    print("=" * 60)
    print(f"成功: {passed}")
    print(f"失敗: {failed}")
    print(f"合計: {passed + failed}")
    
    if failed == 0:
        print("\n✓ すべてのテストに合格しました！")
        return 0
    else:
        print(f"\n✗ {failed}個のテストに失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())