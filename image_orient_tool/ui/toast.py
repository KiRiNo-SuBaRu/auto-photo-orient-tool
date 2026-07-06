# image_orient_tool/ui/toast.py
from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtGui import QPalette


class Toast(QLabel):
    """トースト通知（右下に3秒表示してフェードアウト）"""
    
    def __init__(self, message: str, success: bool = True, parent=None):
        super().__init__(message, parent)
        
        # スタイル設定
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(300)
        self.setMinimumHeight(60)
        self.setWordWrap(True)
        
        if success:
            bg_color = "#4CAF50"  # 緑
        else:
            bg_color = "#f44336"  # 赤
        
        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            border-radius: 10px;
            padding: 15px;
            font-size: 14px;
            font-weight: bold;
        """)
        
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 親ウィンドウの右下に配置
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + parent_rect.width() - self.width() - 20
            y = parent_rect.y() + parent_rect.height() - self.height() - 20
            self.move(x, y)
        
        # フェードアウトアニメーション
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        
        # 3秒後にフェードアウト開始
        QTimer.singleShot(3000, self.fade_animation.start)