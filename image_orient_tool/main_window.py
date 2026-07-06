# image_orient_tool/main_window.py
from pathlib import Path
from typing import Optional, List, Set
import sys
import traceback

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QScrollArea, QGridLayout, QLabel,
    QCheckBox, QRadioButton, QButtonGroup, QProgressBar, QStatusBar,
    QApplication, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QProcess
from PySide6.QtGui import QPixmap, QImage, QKeySequence, QAction, QActionGroup

import cv2
import numpy as np
from PIL import Image

from .core.models import ImageItem
from .core.orientation import load_image_with_exif, rotate_image_bgr, detect_orientation_hybrid
from .core.face_detection import BlazeFaceDetector
from .core.batch_processor import BatchProcessor
from .ui.preview import PreviewDialog
from .ui.toast import Toast
from .util.paths import resource_path
from .settings_manager import SettingsManager
from . import i18n_support as i18n


class ThumbnailWidget(QLabel):
    """サムネイル表示用のクリッカブルなQLabel"""
    clicked = Signal(int, object)  # index, QMouseEvent
    double_clicked = Signal(int)
    
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFrameShape(QLabel.Box)
        self.setLineWidth(3)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(250, 250)
        self.setScaledContents(False)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.index, event)
    
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.index)


class MainWindow(QMainWindow):
    """メインウィンドウ - v3.3完全版"""
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings = settings_manager
        
        # データ
        self.items: List[ImageItem] = []
        self.selected_indices: Set[int] = set()
        self.last_selected_index: Optional[int] = None
        
        # 顔検出
        self.face_detector: Optional[BlazeFaceDetector] = None
        self.face_detection_enabled = False
        
        # UI部品
        self.thumbnail_widgets: List[ThumbnailWidget] = []
        self.status_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # バッチプロセッサ
        self.batch_processor = BatchProcessor()
        
        # UI構築
        self._setup_menu()
        self._setup_ui()
        self._restore_geometry()
        
        # ショートカットキー
        self._setup_shortcuts()
    
    def _setup_menu(self):
        """メニューバー（言語切替など）の構築"""
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu(self.tr("設定"))
        language_menu = settings_menu.addMenu(self.tr("言語 / Language"))

        current_saved = self.settings.load_language()
        language_group = QActionGroup(self)
        language_group.setExclusive(True)

        for code, display_name in i18n.SUPPORTED_LANGUAGES.items():
            action = QAction(display_name, self)
            action.setCheckable(True)
            action.setChecked(code == current_saved)
            action.triggered.connect(lambda checked, c=code: self._on_language_selected(c))
            language_group.addAction(action)
            language_menu.addAction(action)

    def _on_language_selected(self, language_code: str):
        """言語が選択された時の処理（設定保存＋再起動確認）"""
        if language_code == self.settings.load_language():
            return

        self.settings.save_language(language_code)

        ret = QMessageBox.question(
            self,
            self.tr("言語設定"),
            self.tr("言語設定を反映するにはアプリの再起動が必要です。\n今すぐ再起動しますか?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if ret == QMessageBox.Yes:
            self._restart_app()

    def _restart_app(self):
        """アプリケーションを再起動する"""
        self.settings.save_window_geometry(self.saveGeometry())
        QProcess.startDetached(sys.executable, sys.argv)
        QApplication.instance().quit()

    def _setup_ui(self):
        """UI全体の構築"""
        self.setWindowTitle(self.tr("画像向き自動補正ツール v3.3"))
        self.resize(1200, 800)
        
        # 中央ウィジェット
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 上部: オプション群
        options_group = self._create_options_group()
        main_layout.addWidget(options_group)
        
        # 中央: ツールバー
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        
        # 中央: 画像グリッド
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area, stretch=1)
        
        # 下部: プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel(self.tr("画像を読み込んでください"))
        self.status_bar.addWidget(self.status_label)
    
    def _create_options_group(self) -> QGroupBox:
        """オプション設定グループ"""
        group = QGroupBox(self.tr("オプション設定"))
        layout = QHBoxLayout()
        
        # 縦横比モード
        aspect_group = QGroupBox(self.tr("縦横比モード"))
        aspect_layout = QHBoxLayout()
        
        self.aspect_button_group = QButtonGroup()
        self.radio_auto = QRadioButton(self.tr("🔄 自動"))
        self.radio_portrait = QRadioButton(self.tr("📱 縦長"))
        self.radio_landscape = QRadioButton(self.tr("🖥️ 横長"))
        
        self.radio_auto.setChecked(True)
        self.aspect_button_group.addButton(self.radio_auto, 0)
        self.aspect_button_group.addButton(self.radio_portrait, 1)
        self.aspect_button_group.addButton(self.radio_landscape, 2)
        self.aspect_button_group.idClicked.connect(self._on_aspect_mode_changed)
        
        aspect_layout.addWidget(self.radio_auto)
        aspect_layout.addWidget(self.radio_portrait)
        aspect_layout.addWidget(self.radio_landscape)
        aspect_group.setLayout(aspect_layout)
        
        # 顔検出
        face_group = QGroupBox(self.tr("顔検出フィルター"))
        face_layout = QHBoxLayout()
        
        self.face_detection_checkbox = QCheckBox(self.tr("👤 顔検出を有効にする（人物写真の整理に最適）"))
        self.face_detection_checkbox.stateChanged.connect(self._on_face_detection_toggled)
        face_layout.addWidget(self.face_detection_checkbox)
        face_group.setLayout(face_layout)
        
        layout.addWidget(aspect_group)
        layout.addWidget(face_group)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_toolbar(self) -> QHBoxLayout:
        """ツールバーの作成"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # 画像読み込み
        self.btn_load = QPushButton(self.tr("📁 画像を読み込む"))
        self.btn_load.clicked.connect(self.on_load_images)
        self.btn_load.setMinimumHeight(40)
        toolbar.addWidget(self.btn_load)
        
        toolbar.addSpacing(20)
        
        # 回転ボタン
        rotate_label = QLabel(self.tr("手動回転調整:"))
        toolbar.addWidget(rotate_label)
        
        self.btn_rotate_left = QPushButton(self.tr("⟲ 左90°"))
        self.btn_rotate_left.clicked.connect(lambda: self.on_rotate_selected(-90))
        self.btn_rotate_left.setEnabled(False)
        toolbar.addWidget(self.btn_rotate_left)
        
        self.btn_rotate_right = QPushButton(self.tr("⟳ 右90°"))
        self.btn_rotate_right.clicked.connect(lambda: self.on_rotate_selected(90))
        self.btn_rotate_right.setEnabled(False)
        toolbar.addWidget(self.btn_rotate_right)
        
        self.btn_rotate_180 = QPushButton(self.tr("⟲ 180°"))
        self.btn_rotate_180.clicked.connect(lambda: self.on_rotate_selected(180))
        self.btn_rotate_180.setEnabled(False)
        toolbar.addWidget(self.btn_rotate_180)
        
        toolbar.addSpacing(20)
        
        # 選択操作
        self.btn_clear_selection = QPushButton(self.tr("✓ 選択解除"))
        self.btn_clear_selection.clicked.connect(self.on_clear_selection)
        self.btn_clear_selection.setEnabled(False)
        toolbar.addWidget(self.btn_clear_selection)
        
        self.btn_delete = QPushButton(self.tr("🗑️ 選択削除"))
        self.btn_delete.clicked.connect(self.on_delete_selected)
        self.btn_delete.setEnabled(False)
        toolbar.addWidget(self.btn_delete)
        
        toolbar.addSpacing(20)
        
        # 反映ボタン
        self.btn_apply = QPushButton(self.tr("💾 元ファイルに反映する"))
        self.btn_apply.clicked.connect(self.on_apply_changes)
        self.btn_apply.setEnabled(False)
        self.btn_apply.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_apply.setMinimumHeight(40)
        toolbar.addWidget(self.btn_apply)
        
        toolbar.addStretch()
        
        # 選択数表示
        self.selected_count_label = QLabel(self.tr("選択: {0}枚").format(0))
        toolbar.addWidget(self.selected_count_label)
        
        return toolbar
    
    def _setup_shortcuts(self):
        """ショートカットキーの設定"""
        # Delete: 選択削除
        # Ctrl+A: 全選択
        # Escape: 選択解除
        pass  # 後で実装
    
    def _on_face_detection_toggled(self, state):
        """顔検出ON/OFF切り替え"""
        self.face_detection_enabled = (state == Qt.Checked)
        
        if self.face_detection_enabled and self.face_detector is None:
            # 初回ロード
            try:
                model_path = resource_path("resources/models/blazeface.onnx")
                self.face_detector = BlazeFaceDetector(model_path)
                self.face_detector.load()
                self._show_toast(self.tr("✓ 顔検出モデルを読み込みました"), success=True)
            except Exception as e:
                QMessageBox.critical(self, self.tr("エラー"), self.tr("顔検出モデルの読み込みに失敗しました:\n{0}").format(e))
                self.face_detection_checkbox.setChecked(False)
                self.face_detection_enabled = False
    
    # ============================================================
    # 画像読み込み
    # ============================================================
    
    def on_load_images(self):
        """画像ファイルの読み込み"""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("画像を選択"),
            "",
            self.tr("画像ファイル (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)")
        )
        
        if not paths:
            return
        
        # 既存データをクリア
        self._clear_all()
        
        # プログレスバー表示
        self.progress_bar.setMaximum(len(paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # 画像読み込み＋自動判定
        for i, path_str in enumerate(paths):
            try:
                item = self._load_and_process_image(Path(path_str))
                self.items.append(item)
                self._add_thumbnail(len(self.items) - 1)
                
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # UIを更新
                
            except Exception as e:
                QMessageBox.warning(self, self.tr("読み込みエラー"), self.tr("{0} の読み込みに失敗しました:\n{1}").format(Path(path_str).name, e))
        
        self.progress_bar.setVisible(False)
        
        # 顔検出実行（有効な場合）
        if self.face_detection_enabled:
            self._run_face_detection()
        
        self._update_status()
        self._show_toast(self.tr("✓ {0}枚の画像を読み込みました").format(len(self.items)), success=True)
    
    def _load_and_process_image(self, path: Path) -> ImageItem:
        """画像読み込み＋自動向き判定"""
        # EXIF判定
        img_bgr, init_rotation, method = load_image_with_exif(path)
        
        # 初回回転がない場合、ハイブリッド判定を実行
        if init_rotation == 0:
            rotation, method, confidence = detect_orientation_hybrid(img_bgr)
            if rotation != 0:
                img_bgr = rotate_image_bgr(img_bgr, rotation)
                init_rotation = rotation
        
        # 縦横比モード適用
        aspect_mode = self._get_aspect_mode()
        if aspect_mode != "auto":
            img_bgr, additional_rotation = self._apply_aspect_mode(img_bgr, aspect_mode)
            init_rotation = (init_rotation + additional_rotation) % 360
        
        item = ImageItem(
            original_path=path,
            image_array=img_bgr,
            rotation_deg=init_rotation,
            method=method,
            dirty=False,
            delete_pending=False
        )
        
        return item
    
    def _on_aspect_mode_changed(self, button_id: int):
        """縦横比モード（自動/縦長限定/横長限定）が変更された時の処理"""
        # 縦長限定・横長限定モードでは手動90°回転はアスペクト比を崩すため、
        # ボタンの有効/無効状態を再評価する
        self._update_button_states()

    def _get_aspect_mode(self) -> str:
        """縦横比モードの取得"""
        button_id = self.aspect_button_group.checkedId()
        if button_id == 1:
            return "portrait"
        elif button_id == 2:
            return "landscape"
        return "auto"
    
    def _apply_aspect_mode(self, img_bgr: np.ndarray, mode: str) -> tuple:
        """縦横比モードを適用"""
        h, w = img_bgr.shape[:2]
        is_portrait = h > w
        
        additional_rotation = 0
        
        if mode == "portrait" and not is_portrait:
            # 横長を縦長に
            img_bgr = rotate_image_bgr(img_bgr, 90)
            additional_rotation = 90
        elif mode == "landscape" and is_portrait:
            # 縦長を横長に
            img_bgr = rotate_image_bgr(img_bgr, 90)
            additional_rotation = 90
        
        return img_bgr, additional_rotation
    
    def _run_face_detection(self):
        """全画像に対して顔検出を実行"""
        if not self.face_detector:
            return
        
        self.progress_bar.setMaximum(len(self.items))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(self.tr("顔検出実行中..."))
        
        for i, item in enumerate(self.items):
            try:
                detected, count, score = self.face_detector.detect(item.image_array)
                item.face_detected = detected
                item.face_count = count
                item.face_score = score
                
                # 顔未検出なら自動選択
                if not detected:
                    self.selected_indices.add(i)
                    self._update_thumbnail_style(i)
                
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()
                
            except Exception as e:
                print(self.tr("顔検出エラー ({0}): {1}").format(item.original_path.name, e))
        
        self.progress_bar.setVisible(False)
        self._update_status()
        
        # 顔未検出画像の選択通知
        undetected_count = sum(1 for item in self.items if item.face_detected == False)
        if undetected_count > 0:
            self._show_toast(self.tr("⚠ {0}枚で顔が未検出（自動選択）").format(undetected_count), success=False)
    
    # ============================================================
    # サムネイル表示
    # ============================================================
    
    def _add_thumbnail(self, index: int):
        """サムネイルをグリッドに追加"""
        item = self.items[index]
        
        # ThumbnailWidget作成
        thumb = ThumbnailWidget(index)
        thumb.clicked.connect(self._on_thumbnail_clicked)
        thumb.double_clicked.connect(self._on_thumbnail_double_clicked)
        
        # 画像を設定
        self._update_thumbnail_image(thumb, item)
        
        # スタイル設定
        self._update_thumbnail_style(index)
        
        # グリッドに配置（5列）
        row = index // 5
        col = index % 5
        self.grid_layout.addWidget(thumb, row, col)
        
        self.thumbnail_widgets.append(thumb)
    
    def _update_thumbnail_image(self, thumb: ThumbnailWidget, item: ImageItem):
        """サムネイル画像を更新"""
        # BGR → RGB
        img_rgb = cv2.cvtColor(item.image_array, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        
        qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        thumb.setPixmap(pixmap)
        
        # バッジテキスト作成
        badge_text = self._create_badge_text(item)
        thumb.setToolTip(badge_text)
    
    def _method_display_name(self, method: str) -> str:
        """向き判定方法の内部文字列を表示用テキストに変換(翻訳対応)"""
        mapping = {
            "EXIF": self.tr("EXIF"),
            "肌色検出": self.tr("肌色検出"),
            "特徴分析": self.tr("特徴分析"),
            "なし": self.tr("なし"),
            "手動調整": self.tr("手動調整"),
        }
        return mapping.get(method, method)

    def _create_badge_text(self, item: ImageItem) -> str:
        """バッジ用のツールチップテキスト"""
        lines = [
            self.tr("ファイル名: {0}").format(item.original_path.name),
            self.tr("回転: {0}°").format(item.rotation_deg),
            self.tr("判定方法: {0}").format(self._method_display_name(item.method)),
        ]
        
        if item.face_detected is not None:
            if item.face_detected:
                lines.append(self.tr("👤 顔検出: {0}人").format(item.face_count))
            else:
                lines.append(self.tr("❌ 顔未検出"))
        
        if item.dirty:
            lines.append(self.tr("✏️ 変更あり"))
        
        return "\n".join(lines)
    
    def _update_thumbnail_style(self, index: int):
        """サムネイルのスタイル（選択状態）を更新"""
        if index >= len(self.thumbnail_widgets):
            return
        
        thumb = self.thumbnail_widgets[index]
        item = self.items[index]
        
        if index in self.selected_indices:
            # 選択状態: 赤枠
            thumb.setStyleSheet("border: 3px solid red;")
        elif item.face_detected == False:
            # 顔未検出: オレンジ枠
            thumb.setStyleSheet("border: 3px solid orange;")
        elif item.dirty:
            # 変更あり: 青枠
            thumb.setStyleSheet("border: 3px solid blue;")
        else:
            # 通常: グレー枠
            thumb.setStyleSheet("border: 3px solid lightgray;")
    
    # ============================================================
    # 選択操作
    # ============================================================
    
    def _on_thumbnail_clicked(self, index: int, event):
        """サムネイルクリック時の処理"""
        modifiers = event.modifiers()
        
        if modifiers == Qt.ControlModifier:
            # Ctrl+クリック: 追加/解除
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.add(index)
            self.last_selected_index = index
            
        elif modifiers == Qt.ShiftModifier:
            # Shift+クリック: 範囲選択
            if self.last_selected_index is not None:
                start = min(self.last_selected_index, index)
                end = max(self.last_selected_index, index)
                for i in range(start, end + 1):
                    self.selected_indices.add(i)
            else:
                self.selected_indices.add(index)
            self.last_selected_index = index
            
        else:
            # 通常クリック: 単一選択
            self.selected_indices.clear()
            self.selected_indices.add(index)
            self.last_selected_index = index
        
        self._update_all_thumbnail_styles()
        self._update_button_states()
    
    def _on_thumbnail_double_clicked(self, index: int):
        """サムネイルダブルクリック時の処理（プレビュー表示）"""
        if index >= len(self.items):
            return
        
        item = self.items[index]
        dialog = PreviewDialog(item, self)
        dialog.exec()
    
    def on_clear_selection(self):
        """選択解除"""
        self.selected_indices.clear()
        self.last_selected_index = None
        self._update_all_thumbnail_styles()
        self._update_button_states()
    
    def _update_all_thumbnail_styles(self):
        """全サムネイルのスタイルを更新"""
        for i in range(len(self.thumbnail_widgets)):
            self._update_thumbnail_style(i)
    
    # ============================================================
    # 回転操作
    # ============================================================
    
    def on_rotate_selected(self, angle: int):
        """選択画像を回転"""
        if not self.selected_indices:
            return

        # 縦長限定/横長限定モードでは90°回転を禁止（アスペクト比が崩れるため）
        if angle != 180 and self._get_aspect_mode() != "auto":
            self._show_toast(
                self.tr("⚠ 縦長限定/横長限定モードでは90°回転はできません（180°回転のみ可）"),
                success=False
            )
            return
        
        success_indices = []
        failed_items = []
        
        for idx in list(self.selected_indices):
            try:
                item = self.items[idx]
                item.image_array = rotate_image_bgr(item.image_array, angle)
                item.rotation_deg = (item.rotation_deg + angle) % 360
                item.method = "手動調整"
                item.dirty = True
                
                # サムネイル更新
                self._update_thumbnail_image(self.thumbnail_widgets[idx], item)
                
                success_indices.append(idx)
                
            except Exception as e:
                failed_items.append((item.original_path.name, str(e)))
        
        # 成功した画像は選択解除（v3.1仕様）
        for idx in success_indices:
            self.selected_indices.discard(idx)
        
        self._update_all_thumbnail_styles()
        self._update_button_states()
        self._update_status()
        
        # 結果通知
        if success_indices:
            self._show_toast(self.tr("✓ {0}枚の画像を回転しました").format(len(success_indices)), success=True)
        
        if failed_items:
            # 失敗時はダイアログ表示（v3.1仕様）
            error_msg = self.tr("{0}枚の画像の回転処理に失敗しました。\n").format(len(failed_items))
            error_msg += self.tr("失敗した画像は選択状態のまま残っています。\n")
            error_msg += self.tr("再度お試しいただくか、個別に処理してください。\n\n")
            error_msg += self.tr("失敗リスト:\n")
            for name, error in failed_items[:5]:  # 最初の5件だけ表示
                error_msg += self.tr("- {0}: {1}\n").format(name, error)
            
            QMessageBox.warning(self, self.tr("回転エラー"), error_msg)
    
    # ============================================================
    # 削除操作
    # ============================================================
    
    def on_delete_selected(self):
        """選択画像を削除"""
        if not self.selected_indices:
            return
        
        count = len(self.selected_indices)
        ret = QMessageBox.question(
            self,
            self.tr("削除確認"),
            self.tr("選択した{0}枚の画像を削除しますか?\nこの操作は取り消せません。").format(count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret != QMessageBox.Yes:
            return
        
        # 削除予定フラグを立てる
        for idx in self.selected_indices:
            self.items[idx].delete_pending = True
        
        # UIから削除（逆順で削除）
        for idx in sorted(self.selected_indices, reverse=True):
            # サムネイル削除
            thumb = self.thumbnail_widgets[idx]
            self.grid_layout.removeWidget(thumb)
            thumb.deleteLater()
            
            # リストから削除
            del self.thumbnail_widgets[idx]
            del self.items[idx]
        
        # インデックスを再割り当て
        for i, thumb in enumerate(self.thumbnail_widgets):
            thumb.index = i
            row = i // 5
            col = i % 5
            self.grid_layout.addWidget(thumb, row, col)
        
        self.selected_indices.clear()
        self.last_selected_index = None
        
        self._update_button_states()
        self._update_status()
        self._show_toast(self.tr("✓ {0}枚の画像を削除しました").format(count), success=True)
    
    # ============================================================
    # 元ファイルに反映
    # ============================================================
    
    def on_apply_changes(self):
        """元ファイルに変更を反映"""
        # 変更内容を集計
        dirty_items = [item for item in self.items if item.dirty and not item.delete_pending]
        delete_items = [item for item in self.items if item.delete_pending]
        
        if not dirty_items and not delete_items:
            QMessageBox.information(self, self.tr("情報"), self.tr("元ファイルに反映する変更はありません。"))
            return
        
        # 確認ダイアログ
        msg = self.tr("すべての変更を元ファイルに反映しますか?\n\n")
        if dirty_items:
            msg += self.tr("・回転した画像: {0}枚（上書き保存されます）\n").format(len(dirty_items))
        if delete_items:
            msg += self.tr("・削除した画像: {0}枚（元ファイルも削除されます）\n").format(len(delete_items))
        msg += self.tr("\nこの操作は取り消せません。")
        
        ret = QMessageBox.question(
            self,
            self.tr("変更を反映"),
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret != QMessageBox.Yes:
            return
        
        # 反映処理
        self.progress_bar.setMaximum(len(dirty_items) + len(delete_items))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(self.tr("元ファイルに反映中..."))
        
        save_errors = []
        delete_errors = []
        
        # 1. 回転した画像を保存
        for i, item in enumerate(dirty_items):
            try:
                self._save_image_to_file(item)
                item.dirty = False
            except Exception as e:
                save_errors.append((item.original_path.name, str(e)))
            
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        
        # 2. 削除予定の画像を削除
        for i, item in enumerate(delete_items):
            try:
                item.original_path.unlink()  # ファイル削除
            except Exception as e:
                delete_errors.append((item.original_path.name, str(e)))
            
            self.progress_bar.setValue(len(dirty_items) + i + 1)
            QApplication.processEvents()
        
        self.progress_bar.setVisible(False)
        
        # 結果通知
        success_count = len(dirty_items) - len(save_errors) + len(delete_items) - len(delete_errors)
        
        if not save_errors and not delete_errors:
            self._show_toast(self.tr("✓ {0}件の変更を元ファイルに反映しました").format(success_count), success=True)
            self._update_status()
        else:
            # エラー通知
            error_msg = self.tr("{0}件の変更を反映しました。\n\n").format(success_count)
            if save_errors:
                error_msg += self.tr("保存失敗: {0}件\n").format(len(save_errors))
                for name, err in save_errors[:3]:
                    error_msg += self.tr("- {0}: {1}\n").format(name, err)
            if delete_errors:
                error_msg += self.tr("\n削除失敗: {0}件\n").format(len(delete_errors))
                for name, err in delete_errors[:3]:
                    error_msg += self.tr("- {0}: {1}\n").format(name, err)
            
            QMessageBox.warning(self, self.tr("一部エラー"), error_msg)
    
    def _save_image_to_file(self, item: ImageItem):
        """画像をファイルに保存（EXIF Orientation更新）"""
        # BGRからRGBに変換
        img_rgb = cv2.cvtColor(item.image_array, cv2.COLOR_BGR2RGB)
        
        # Pillow Imageに変換
        pil_img = Image.fromarray(img_rgb)
        
        # EXIF情報を読み込み
        try:
            exif = pil_img.getexif()
            # Orientationタグを正方向（1）に設定
            exif[0x0112] = 1  # Orientation
            pil_img.save(item.original_path, exif=exif)
        except:
            # EXIFなしで保存
            pil_img.save(item.original_path)
    
    # ============================================================
    # UI更新
    # ============================================================
    
    def _update_button_states(self):
        """ボタンの有効/無効状態を更新"""
        has_selection = len(self.selected_indices) > 0
        has_items = len(self.items) > 0
        has_changes = any(item.dirty for item in self.items)

        # 縦長限定/横長限定モードでは、90°回転はアスペクト比（縦長⇔横長）を
        # 崩してしまうため無効化し、180°回転のみ許可する
        aspect_mode = self._get_aspect_mode()
        rotate_90_allowed = has_selection and aspect_mode == "auto"

        self.btn_rotate_left.setEnabled(rotate_90_allowed)
        self.btn_rotate_right.setEnabled(rotate_90_allowed)
        self.btn_rotate_180.setEnabled(has_selection)

        if aspect_mode != "auto":
            restriction_tooltip = self.tr(
                "縦長限定/横長限定モードでは、90°回転はアスペクト比を崩すため無効です。\n"
                "180°回転は引き続き使用できます。"
            )
        else:
            restriction_tooltip = ""
        self.btn_rotate_left.setToolTip(restriction_tooltip)
        self.btn_rotate_right.setToolTip(restriction_tooltip)

        self.btn_clear_selection.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_apply.setEnabled(has_changes)
        
        self.selected_count_label.setText(self.tr("選択: {0}枚").format(len(self.selected_indices)))
    
    def _update_status(self):
        """ステータスバーを更新"""
        total = len(self.items)
        dirty = sum(1 for item in self.items if item.dirty)
        selected = len(self.selected_indices)
        
        status = self.tr("総画像数: {0}枚").format(total)
        if dirty > 0:
            status += self.tr(" | 変更: {0}枚").format(dirty)
        if selected > 0:
            status += self.tr(" | 選択: {0}枚").format(selected)
        
        if self.face_detection_enabled:
            detected = sum(1 for item in self.items if item.face_detected == True)
            undetected = sum(1 for item in self.items if item.face_detected == False)
            status += self.tr(" | 顔検出: {0}枚 / 未検出: {1}枚").format(detected, undetected)
        
        self.status_label.setText(status)
        self._update_button_states()
    
    # ============================================================
    # ユーティリティ
    # ============================================================
    
    def _clear_all(self):
        """全データをクリア"""
        self.items.clear()
        self.selected_indices.clear()
        self.last_selected_index = None
        
        # UI削除
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.thumbnail_widgets.clear()
        self._update_status()
    
    def _show_toast(self, message: str, success: bool = True):
        """トースト通知を表示"""
        toast = Toast(message, success, self)
        toast.show()
    
    def _restore_geometry(self):
        """ウィンドウ位置・サイズを復元"""
        geometry = self.settings.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
    
    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理"""
        # 未保存の変更があれば警告
        has_changes = any(item.dirty for item in self.items)
        if has_changes:
            ret = QMessageBox.question(
                self,
                self.tr("未保存の変更"),
                self.tr("元ファイルに反映していない変更があります。\nこのまま終了しますか?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                event.ignore()
                return
        
        # ウィンドウ状態を保存
        self.settings.save_window_geometry(self.saveGeometry())
        event.accept()