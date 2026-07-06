# image_orient_tool/core/orientation.py
"""
画像の向き判定モジュール
3段階ハイブリッド判定: EXIF → 肌色検出 → 特徴分析
"""
from pathlib import Path
from typing import Tuple
import numpy as np
import cv2
from PIL import Image, ExifTags


def load_image_with_exif(path: Path) -> Tuple[np.ndarray, int, str]:
    """
    画像を読み込み、EXIFから向きを判定して回転
    
    Args:
        path: 画像ファイルのパス
        
    Returns:
        (BGR画像, 回転角度, 判定方法)
    """
    # Pillowで読み込み
    pil_img = Image.open(path)
    
    # EXIF情報を取得
    try:
        exif = pil_img.getexif()
        orientation = 1  # デフォルト（正常）
        
        # Orientationタグを探す
        for tag_id, tag_name in ExifTags.TAGS.items():
            if tag_name == "Orientation":
                orientation = exif.get(tag_id, 1)
                break
        
        # Orientationに応じた回転角度を決定
        rotation_deg = 0
        if orientation == 3:
            rotation_deg = 180
        elif orientation == 6:
            rotation_deg = 270  # 右に90度回転（時計回り）
        elif orientation == 8:
            rotation_deg = 90   # 左に90度回転（反時計回り）
        
        if rotation_deg != 0:
            # EXIFで回転が必要
            img_rgb = np.array(pil_img.convert("RGB"))
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_bgr = rotate_image_bgr(img_bgr, rotation_deg)
            return img_bgr, rotation_deg, "EXIF"
    
    except Exception as e:
        # EXIF読み取りエラー
        pass
    
    # EXIFがない、または回転不要
    img_rgb = np.array(pil_img.convert("RGB"))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    return img_bgr, 0, "なし"


def rotate_image_bgr(img_bgr: np.ndarray, angle: int) -> np.ndarray:
    """
    画像を90度刻みで回転
    
    Args:
        img_bgr: OpenCV BGR画像
        angle: 回転角度（90, 180, 270, -90など）
        
    Returns:
        回転後の画像
    """
    angle = angle % 360
    
    if angle == 0:
        return img_bgr
    elif angle == 90 or angle == -270:
        return cv2.rotate(img_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif angle == 180 or angle == -180:
        return cv2.rotate(img_bgr, cv2.ROTATE_180)
    elif angle == 270 or angle == -90:
        return cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
    
    return img_bgr


def detect_orientation_hybrid(img_bgr: np.ndarray, 
                               resize_max: int = 640) -> Tuple[int, str, float]:
    """
    ハイブリッド向き判定（肌色検出 → 特徴分析）
    
    Args:
        img_bgr: OpenCV BGR画像
        resize_max: 処理用リサイズ最大サイズ（高速化）
        
    Returns:
        (回転角度, 判定方法, 信頼度)
    """
    # 処理高速化のため縮小
    h, w = img_bgr.shape[:2]
    if max(h, w) > resize_max:
        scale = resize_max / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img_small = cv2.resize(img_bgr, (new_w, new_h))
    else:
        img_small = img_bgr
    
    # 第2段階: 肌色検出
    rotation, confidence = detect_skin_orientation(img_small)
    if confidence >= 0.6:
        return rotation, "肌色検出", confidence
    
    # 第3段階: 特徴分析
    rotation, confidence = detect_feature_orientation(img_small)
    return rotation, "特徴分析", confidence


def detect_skin_orientation(img_bgr: np.ndarray) -> Tuple[int, float]:
    """
    肌色領域の位置から向きを判定
    
    Args:
        img_bgr: OpenCV BGR画像
        
    Returns:
        (回転角度, 信頼度)
    """
    # YCrCb色空間に変換
    img_ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    
    # 肌色範囲（YCrCb空間）
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    
    # 肌色マスクを生成
    skin_mask = cv2.inRange(img_ycrcb, lower_skin, upper_skin)
    
    # ノイズ除去
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel, iterations=2)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # ぼかし
    skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)
    
    # 肌色ピクセルの総数
    total_skin = np.sum(skin_mask > 0)
    
    if total_skin < 100:
        # 肌色が少なすぎる
        return 0, 0.0
    
    # 画像を4分割して、各領域の肌色密度を計算
    h, w = img_bgr.shape[:2]
    scores = {}
    
    for angle in [0, 90, 180, 270]:
        rotated_mask = rotate_image_bgr(skin_mask, angle)
        h_rot, w_rot = rotated_mask.shape[:2]
        
        # 上半分の肌色密度
        top_half = rotated_mask[:h_rot//2, :]
        top_density = np.sum(top_half > 0) / (h_rot * w_rot / 2)
        
        # 上部25%の肌色密度
        top_quarter = rotated_mask[:h_rot//4, :]
        top_quarter_density = np.sum(top_quarter > 0) / (h_rot * w_rot / 4)
        
        # スコア: 上部に肌色が多いほど高い
        score = top_quarter_density * 0.7 + top_density * 0.3
        scores[angle] = score
    
    # 最もスコアが高い角度を選択
    best_angle = max(scores, key=scores.get)
    confidence = scores[best_angle]
    
    # 信頼度の正規化（0.0〜1.0）
    confidence = min(confidence * 5, 1.0)
    
    return best_angle, confidence


def detect_feature_orientation(img_bgr: np.ndarray) -> Tuple[int, float]:
    """
    画像特徴から向きを判定
    
    明るさ分布、エッジ方向性、色分布、テクスチャ複雑さを総合評価
    
    Args:
        img_bgr: OpenCV BGR画像
        
    Returns:
        (回転角度, 信頼度)
    """
    scores = {}
    
    for angle in [0, 90, 180, 270]:
        rotated = rotate_image_bgr(img_bgr, angle)
        
        # 各特徴のスコアを計算
        brightness_score = _analyze_brightness(rotated)
        edge_score = _analyze_edges(rotated)
        color_score = _analyze_color(rotated)
        texture_score = _analyze_texture(rotated)
        
        # 総合スコア（重み付け平均）
        total_score = (
            brightness_score * 0.3 +
            edge_score * 0.2 +
            color_score * 0.3 +
            texture_score * 0.2
        )
        
        scores[angle] = total_score
    
    # 最もスコアが高い角度を選択
    best_angle = max(scores, key=scores.get)
    confidence = scores[best_angle]
    
    # 信頼度の正規化
    confidence = min(confidence / 100, 1.0)
    
    return best_angle, confidence


def _analyze_brightness(img_bgr: np.ndarray) -> float:
    """明るさ分布を分析（空は上、地面は下）"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # 上半分と下半分の平均明るさ
    top_brightness = np.mean(gray[:h//2, :])
    bottom_brightness = np.mean(gray[h//2:, :])
    
    # 上が明るいほど高スコア
    score = (top_brightness - bottom_brightness) + 50
    return max(0, score)


def _analyze_edges(img_bgr: np.ndarray) -> float:
    """エッジ方向性を分析（水平エッジが多いのが自然）"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Sobelエッジ検出
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # 水平エッジと垂直エッジの強度
    horizontal_edges = np.sum(np.abs(sobely))
    vertical_edges = np.sum(np.abs(sobelx))
    
    # 水平エッジが多いほど高スコア
    if vertical_edges > 0:
        score = (horizontal_edges / vertical_edges) * 30
    else:
        score = 50
    
    return min(score, 100)


def _analyze_color(img_bgr: np.ndarray) -> float:
    """色分布を分析（青空は上部に多い）"""
    h, w = img_bgr.shape[:2]
    
    # 上半分の青成分の平均
    top_blue = np.mean(img_bgr[:h//2, :, 0])  # BGR形式なのでindex 0が青
    
    # 下半分の青成分の平均
    bottom_blue = np.mean(img_bgr[h//2:, :, 0])
    
    # 上部に青が多いほど高スコア
    score = (top_blue - bottom_blue) + 50
    return max(0, score)


def _analyze_texture(img_bgr: np.ndarray) -> float:
    """テクスチャ複雑さを分析（下部がより複雑な傾向）"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # ラプラシアンで複雑さを測定
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    
    # 上半分と下半分の複雑さ
    top_complexity = np.var(laplacian[:h//2, :])
    bottom_complexity = np.var(laplacian[h//2:, :])
    
    # 下部がより複雑なほど高スコア
    if top_complexity > 0:
        score = (bottom_complexity / top_complexity) * 30
    else:
        score = 50
    
    return min(score, 100)