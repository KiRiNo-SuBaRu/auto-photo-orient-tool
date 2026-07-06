# image_orient_tool/core/models.py
"""
アプリ全体で使うデータモデル
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np


@dataclass
class ImageItem:
    """1枚の画像を表すデータモデル"""
    original_path: Path          # 元ファイルパス
    image_array: np.ndarray      # 現在の画像 (BGR, OpenCV形式)
    rotation_deg: int = 0        # 累計回転角度
    method: str = "EXIF"         # 向き判定方法 ("EXIF" / "肌色検出" / "特徴分析" / "なし" / "手動")
    face_detected: Optional[bool] = None
    face_count: int = 0
    face_score: float = 0.0
    dirty: bool = False          # 変更あり（未反映の回転など）
    delete_pending: bool = False # 削除予定
