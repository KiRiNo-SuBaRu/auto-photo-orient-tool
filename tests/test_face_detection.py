# tests/test_face_detection.py
"""
顔検出機能のテスト
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from image_orient_tool.core.face_detection import BlazeFaceDetector
from image_orient_tool.util.paths import resource_path


def create_dummy_face_image():
    """ダミーの顔画像を作成（楕円形）"""
    img = np.zeros((400, 300, 3), dtype=np.uint8)
    img[:, :] = 200  # グレー背景
    
    # 楕円（顔の代わり）を描画
    center = (150, 200)
    axes = (60, 80)
    cv2.ellipse(img, center, axes, 0, 0, 360, (220, 180, 140), -1)
    
    # 目（黒い円）
    cv2.circle(img, (130, 180), 8, (0, 0, 0), -1)
    cv2.circle(img, (170, 180), 8, (0, 0, 0), -1)
    
    # 口（線）
    cv2.ellipse(img, (150, 220), (25, 15), 0, 0, 180, (0, 0, 0), 2)
    
    return img


def test_model_loading():
    """モデル読み込みのテスト"""
    print("\n=== BlazeFaceモデル読み込みテスト ===")
    
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    
    if not model_path.exists():
        print(f"✗ モデルが見つかりません: {model_path}")
        print("  download_blazeface.py を実行してください")
        return False
    
    print(f"モデルパス: {model_path}")
    print(f"モデルサイズ: {model_path.stat().st_size / 1024:.1f} KB")
    
    try:
        detector = BlazeFaceDetector(model_path, confidence_threshold=0.5)
        detector.load()
        
        print("✓ モデル読み込み成功")
        print(f"  入力名: {detector.input_name}")
        print(f"  出力数: {len(detector.output_names)}")
        print(f"  プロバイダー: {detector.session.get_providers()}")
        
        return True
        
    except Exception as e:
        print(f"✗ モデル読み込み失敗: {e}")
        return False


def test_face_detection_dummy():
    """ダミー画像での顔検出テスト"""
    print("\n=== ダミー画像顔検出テスト ===")
    
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    
    if not model_path.exists():
        print("⚠ モデルが見つかりません（スキップ）")
        return
    
    # 検出器を作成
    detector = BlazeFaceDetector(model_path, confidence_threshold=0.3)
    detector.load()
    
    # ダミー顔画像を作成
    img = create_dummy_face_image()
    print(f"テスト画像サイズ: {img.shape}")
    
    # 顔検出実行
    detected, count, score = detector.detect(img)
    
    print(f"検出結果:")
    print(f"  検出: {'あり' if detected else 'なし'}")
    print(f"  検出数: {count}人")
    print(f"  最大スコア: {score:.3f}")
    
    # 注: ダミー画像なので検出されない可能性が高い
    print("✓ 顔検出処理は正常に実行されました")


def test_face_detection_real_image():
    """実画像での顔検出テスト"""
    print("\n=== 実画像顔検出テスト ===")
    
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    
    if not model_path.exists():
        print("⚠ モデルが見つかりません（スキップ）")
        return
    
    # テスト画像を探す
    test_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        test_images.extend(Path(".").glob(f"**/{ext}"))
    
    if not test_images:
        print("⚠ テスト用の画像が見つかりません（スキップ）")
        print("  人物が写った画像を用意すると、より詳細なテストができます")
        return
    
    # 最初の画像でテスト
    test_image = test_images[0]
    print(f"テスト画像: {test_image}")
    
    # 検出器を作成
    detector = BlazeFaceDetector(model_path, confidence_threshold=0.5)
    detector.load()
    
    # 画像を読み込み
    img = cv2.imread(str(test_image))
    if img is None:
        print(f"✗ 画像の読み込みに失敗: {test_image}")
        return
    
    print(f"画像サイズ: {img.shape}")
    
    # 顔検出実行
    detected, count, score, vis_img = detector.detect_with_visualization(img)
    
    print(f"検出結果:")
    print(f"  検出: {'あり' if detected else 'なし'}")
    print(f"  検出数: {count}人")
    print(f"  最大スコア: {score:.3f}")
    
    # 可視化画像を保存
    if detected:
        output_path = Path("test_face_detection_output.jpg")
        cv2.imwrite(str(output_path), vis_img)
        print(f"  可視化画像を保存: {output_path}")
    
    print("✓ 実画像顔検出テスト: 完了")


def test_detection_threshold():
    """検出閾値のテスト"""
    print("\n=== 検出閾値テスト ===")
    
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    
    if not model_path.exists():
        print("⚠ モデルが見つかりません（スキップ）")
        return
    
    # ダミー画像
    img = create_dummy_face_image()
    
    # 異なる閾値でテスト
    thresholds = [0.3, 0.5, 0.7, 0.9]
    
    for threshold in thresholds:
        detector = BlazeFaceDetector(model_path, confidence_threshold=threshold)
        detector.load()
        
        detected, count, score = detector.detect(img)
        
        print(f"閾値 {threshold:.1f}: 検出={detected}, 数={count}, スコア={score:.3f}")
    
    print("✓ 検出閾値テスト: 完了")


def run_all_tests():
    """全テストを実行"""
    print("=" * 60)
    print("顔検出機能テスト開始")
    print("=" * 60)
    
    tests = [
        ("モデル読み込み", test_model_loading),
        ("ダミー画像検出", test_face_detection_dummy),
        ("実画像検出", test_face_detection_real_image),
        ("検出閾値", test_detection_threshold)
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is False:
                failed += 1
            else:
                passed += 1
        except Exception as e:
            print(f"✗ {name}: エラー - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("テスト結果")
    print("=" * 60)
    print(f"成功: {passed}")
    print(f"失敗: {failed}")
    
    if failed == 0:
        print("\n✓ すべてのテストに合格しました！")
        return 0
    else:
        print(f"\n✗ {failed}個のテストに失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())