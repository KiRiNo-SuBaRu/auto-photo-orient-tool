# tests/test_gui_basic.py
"""
GUI基本機能のテスト（pytest-qt使用）
"""
import sys
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from image_orient_tool.settings_manager import SettingsManager
from image_orient_tool.main_window import MainWindow


@pytest.fixture
def app(qtbot):
    """QApplicationフィクスチャ"""
    test_app = QApplication.instance()
    if test_app is None:
        test_app = QApplication(sys.argv)
    return test_app


@pytest.fixture
def main_window(qtbot, app):
    """MainWindowフィクスチャ"""
    settings = SettingsManager()
    window = MainWindow(settings)
    qtbot.addWidget(window)
    return window


def test_window_creation(main_window):
    """ウィンドウ作成のテスト"""
    assert main_window is not None
    assert main_window.windowTitle() == "画像向き自動補正ツール v3.3"
    print("✓ ウィンドウ作成: 成功")


def test_initial_button_states(main_window):
    """初期ボタン状態のテスト"""
    # 画像未読み込み時はボタンが無効
    assert main_window.btn_load.isEnabled() == True
    assert main_window.btn_rotate_left.isEnabled() == False
    assert main_window.btn_rotate_right.isEnabled() == False
    assert main_window.btn_rotate_180.isEnabled() == False
    assert main_window.btn_delete.isEnabled() == False
    assert main_window.btn_apply.isEnabled() == False
    print("✓ 初期ボタン状態: 正常")


def test_aspect_mode_selection(main_window):
    """縦横比モード選択のテスト"""
    # 初期状態は自動
    assert main_window.radio_auto.isChecked() == True
    
    # 縦長モードに変更
    main_window.radio_portrait.setChecked(True)
    assert main_window._get_aspect_mode() == "portrait"
    
    # 横長モードに変更
    main_window.radio_landscape.setChecked(True)
    assert main_window._get_aspect_mode() == "landscape"
    
    # 自動モードに戻す
    main_window.radio_auto.setChecked(True)
    assert main_window._get_aspect_mode() == "auto"
    
    print("✓ 縦横比モード選択: 正常")


def test_apply_aspect_mode_rotates_correctly(main_window):
    """
    縦横比モード(_apply_aspect_mode)が実際に画像を正しい向きへ
    回転させているかを検証する
    """
    import numpy as np

    landscape_img = np.zeros((300, 400, 3), dtype=np.uint8)  # h=300 < w=400
    portrait_img = np.zeros((400, 300, 3), dtype=np.uint8)   # h=400 > w=300

    # 縦長限定モード: 横長画像は90°回転されて縦長になるべき
    out, rot = main_window._apply_aspect_mode(landscape_img, "portrait")
    h, w = out.shape[:2]
    assert h > w, "縦長限定モードで横長画像が縦長に変換されていない"
    assert rot == 90

    # 縦長限定モード: すでに縦長の画像は変更されないべき
    out, rot = main_window._apply_aspect_mode(portrait_img, "portrait")
    h, w = out.shape[:2]
    assert h > w
    assert rot == 0

    # 横長限定モード: 縦長画像は90°回転されて横長になるべき
    out, rot = main_window._apply_aspect_mode(portrait_img, "landscape")
    h, w = out.shape[:2]
    assert w > h, "横長限定モードで縦長画像が横長に変換されていない"
    assert rot == 90

    # 横長限定モード: すでに横長の画像は変更されないべき
    out, rot = main_window._apply_aspect_mode(landscape_img, "landscape")
    h, w = out.shape[:2]
    assert w > h
    assert rot == 0

    print("✓ 縦横比モードの画像回転ロジック: 正常")


def test_90_degree_rotation_disabled_in_restricted_mode(main_window):
    """
    縦長限定/横長限定モードでは、手動90°回転ボタンが無効化され、
    180°回転のみ有効なままであることを検証する
    """
    # 選択状態を1件作ったことにする（サムネイル自体は無くてもボタン状態判定は可能）
    main_window.selected_indices = {0}

    # 自動モードでは90°回転ボタンが有効
    main_window.radio_auto.setChecked(True)
    main_window._update_button_states()
    assert main_window.btn_rotate_left.isEnabled() == True
    assert main_window.btn_rotate_right.isEnabled() == True
    assert main_window.btn_rotate_180.isEnabled() == True

    # 縦長限定モードでは90°回転ボタンが無効、180°回転は有効のまま
    main_window.radio_portrait.setChecked(True)
    main_window._update_button_states()
    assert main_window.btn_rotate_left.isEnabled() == False
    assert main_window.btn_rotate_right.isEnabled() == False
    assert main_window.btn_rotate_180.isEnabled() == True

    # 横長限定モードでも同様
    main_window.radio_landscape.setChecked(True)
    main_window._update_button_states()
    assert main_window.btn_rotate_left.isEnabled() == False
    assert main_window.btn_rotate_right.isEnabled() == False
    assert main_window.btn_rotate_180.isEnabled() == True

    # 自動モードに戻すと再び90°回転ボタンが有効になる
    main_window.radio_auto.setChecked(True)
    main_window._update_button_states()
    assert main_window.btn_rotate_left.isEnabled() == True
    assert main_window.btn_rotate_right.isEnabled() == True

    # 後片付け（他テストへの影響防止）
    main_window.selected_indices = set()

    print("✓ 縦長限定/横長限定モードでの90°回転制限: 正常")


def test_on_rotate_selected_rejects_90_degree_in_restricted_mode(main_window, monkeypatch):
    """
    on_rotate_selected(90)/on_rotate_selected(-90) が、縦横比限定モード中は
    何も変更せずに拒否される（180°のみ許可）ことを検証する
    """
    import numpy as np
    from image_orient_tool.core.models import ImageItem
    from pathlib import Path as P

    item = ImageItem(
        original_path=P("dummy.jpg"),
        image_array=np.zeros((300, 400, 3), dtype=np.uint8),
        rotation_deg=0,
        method="EXIF",
        dirty=False,
        delete_pending=False,
    )
    main_window.items = [item]
    main_window.selected_indices = {0}
    main_window.thumbnail_widgets = []  # 更新処理をスキップさせるため空にする

    # サムネイル更新をno-opにして、存在しないウィジェットへのアクセスを回避
    monkeypatch.setattr(main_window, "_update_thumbnail_image", lambda *a, **kw: None)
    monkeypatch.setattr(main_window, "_update_all_thumbnail_styles", lambda: None)

    main_window.radio_portrait.setChecked(True)

    main_window.on_rotate_selected(90)
    assert item.dirty == False, "縦長限定モードで90°回転が実行されてしまった"
    assert item.rotation_deg == 0

    main_window.on_rotate_selected(180)
    assert item.dirty == True, "縦長限定モードでも180°回転は許可されるべき"
    assert item.rotation_deg == 180

    # 後片付け
    main_window.items = []
    main_window.selected_indices = set()
    main_window.radio_auto.setChecked(True)

    print("✓ on_rotate_selected の90°回転拒否: 正常")


def test_face_detection_toggle(main_window):
    """顔検出ON/OFF切り替えのテスト"""
    # 初期状態はOFF
    assert main_window.face_detection_enabled == False
    
    # ONに切り替え（モデルがない場合はスキップ）
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")
    if model_path.exists():
        main_window.face_detection_checkbox.setChecked(True)
        assert main_window.face_detection_enabled == True
        print("✓ 顔検出ON/OFF切り替え: 正常")
    else:
        print("⚠ 顔検出テスト: モデルがないためスキップ")


def test_status_update(main_window):
    """ステータス更新のテスト"""
    main_window._update_status()
    status_text = main_window.status_label.text()
    assert "総画像数" in status_text or "画像を読み込んでください" in status_text
    print("✓ ステータス更新: 正常")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])