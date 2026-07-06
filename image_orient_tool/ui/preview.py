# image_orient_tool/ui/preview.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QWheelEvent
import cv2
import numpy as np

from ..core.models import ImageItem


class PreviewDialog(QDialog):
    """画像プレビューダイアログ（ズーム機能付き）"""
    
    def __init__(self, item: ImageItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.zoom_level = 1.0
        
        self.setWindowTitle(self.tr("プレビュー - {0}").format(item.original_path.name))
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # スクロールエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # ボタン群
        btn_layout = QHBoxLayout()
        
        btn_zoom_in = QPushButton(self.tr("🔍 ズームイン"))
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_layout.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton(self.tr("🔍 ズームアウト"))
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_layout.addWidget(btn_zoom_out)
        
        btn_reset = QPushButton(self.tr("🔄 リセット"))
        btn_reset.clicked.connect(self.zoom_reset)
        btn_layout.addWidget(btn_reset)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton(self.tr("閉じる"))
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # 初期表示
        self._update_image()
        
        # ホイールイベント
        self.scroll_area.wheelEvent = self._wheel_event
    
    def _update_image(self):
        """画像を更新"""
        img_rgb = cv2.cvtColor(self.item.image_array, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        
        qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # ズーム適用
        scaled_w = int(w * self.zoom_level)
        scaled_h = int(h * self.zoom_level)
        
        pixmap = QPixmap.fromImage(qimg).scaled(
            scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(pixmap)
        self.setWindowTitle(self.tr("プレビュー - {0} ({1}%)").format(self.item.original_path.name, int(self.zoom_level * 100)))
    
    def zoom_in(self):
        """ズームイン"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self._update_image()
    
    def zoom_out(self):
        """ズームアウト"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self._update_image()
    
    def zoom_reset(self):
        """ズームリセット"""
        self.zoom_level = 1.0
        self._update_image()
    
    def _wheel_event(self, event: QWheelEvent):
        """Ctrl+ホイールでズーム"""
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # 通常のスクロール
            QScrollArea.wheelEvent(self.scroll_area, event)