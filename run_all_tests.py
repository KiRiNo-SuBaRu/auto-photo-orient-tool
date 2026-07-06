# run_all_tests.py
"""
全テストを順番に実行するスクリプト
"""
import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: Path):
    """テストファイルを実行"""
    print("\n" + "=" * 70)
    print(f"実行中: {test_file.name}")
    print("=" * 70)
    
    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    """メイン処理"""
    print("=" * 70)
    print("画像向き自動補正ツール v3.3 - 全体統合テスト")
    print("=" * 70)
    
    tests_dir = Path(__file__).parent / "tests"
    
    # 実行するテスト一覧（順番重要）
    test_files = [
        "test_basic_functionality.py",
        "test_face_detection.py",
        # "test_gui_basic.py"  # pytest-qtが必要
    ]
    
    results = {}
    
    for test_file_name in test_files:
        test_file = tests_dir / test_file_name
        
        if not test_file.exists():
            print(f"⚠ テストファイルが見つかりません: {test_file}")
            results[test_file_name] = None
            continue
        
        success = run_test_file(test_file)
        results[test_file_name] = success
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v == True)
    failed = sum(1 for v in results.values() if v == False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ 成功"
        elif result is False:
            status = "✗ 失敗"
        else:
            status = "⚠ スキップ"
        
        print(f"{test_name:40s}: {status}")
    
    print("\n" + "=" * 70)
    print(f"成功: {passed} / 失敗: {failed} / スキップ: {skipped}")
    print("=" * 70)
    
    if failed == 0:
        print("\n✓ すべてのテストに合格しました！")
        print("  python run.py でアプリを起動できます")
        return 0
    else:
        print(f"\n✗ {failed}個のテストに失敗しました")
        print("  エラーを確認して修正してください")
        return 1


if __name__ == "__main__":
    sys.exit(main())