# image_orient_tool/core/face_detection.py
from pathlib import Path
from typing import Tuple, Optional, List, Dict
import numpy as np
import cv2
import onnxruntime as ort


class BlazeFaceDetector:
    """
    BlazeFace ONNX顔検出器

    使用モデル: https://huggingface.co/garavv/blazeface-onnx (blaze.onnx)
    このモデルは内部でNMS（Non-Max Suppression）まで実行済みの検出結果を返す
    "オールインワン"型のONNXモデルで、以下の4つの入力を取る:

        - "image":          (1, 3, 128, 128) float32, 0.0〜1.0に正規化されたRGB画像
        - "conf_threshold":  (1,) float32
        - "max_detections":  (1,) int64
        - "iou_threshold":   (1,) float32

    出力は2つ:
        - outs[0]: (1, N, 16) 各顔の [top_y, top_x, bot_y, bot_x, 6組の顔ランドマークx,y]
                   （すべて0〜1に正規化された座標）
        - outs[1]: (1, N)     各顔の信頼度スコア
    """

    def __init__(self, model_path: Path, confidence_threshold: float = 0.5):
        """
        Args:
            model_path: BlazeFace ONNXモデルのパス
            confidence_threshold: 検出信頼度の閾値（0.0〜1.0）
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.session: Optional[ort.InferenceSession] = None

        # 入力サイズ（BlazeFaceは128x128）
        self.input_size = (128, 128)

        # モデル内蔵NMSのパラメータ
        self.max_detections = 25
        self.iou_threshold = 0.3

        # セッション設定
        self.sess_options = ort.SessionOptions()
        self.sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        # このモデルは出力形状のメタデータが (1, 896, 16) 固定で宣言されている一方、
        # 実際の出力は検出数に応じて可変のため、無害な形状不一致の警告(W)が出る。
        # ログレベルをERROR(3)にして警告を抑制する。
        self.sess_options.log_severity_level = 3

        # プロバイダー（CPU/GPU）
        self.providers = ['CPUExecutionProvider']

        # GPU利用可能ならCUDAを優先
        available_providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' in available_providers:
            self.providers.insert(0, 'CUDAExecutionProvider')

        # 入出力名（load()後に設定される）
        self.input_name = "image"
        self.output_names: List[str] = []

    def load(self):
        """モデルを読み込む"""
        if self.session is not None:
            return  # 既にロード済み

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"BlazeFaceモデルが見つかりません: {self.model_path}\n"
                f"download_blazeface.pyを実行してモデルをダウンロードしてください。"
            )

        try:
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=self.sess_options,
                providers=self.providers
            )

            # 入出力情報を取得
            input_names = [inp.name for inp in self.session.get_inputs()]
            if "image" in input_names:
                self.input_name = "image"
            else:
                # モデルの入力名が想定と違う場合は最初の入力を使う
                self.input_name = input_names[0]

            self.output_names = [output.name for output in self.session.get_outputs()]

            print(f"✓ BlazeFaceモデルをロードしました")
            print(f"  入力: {', '.join(input_names)}")
            print(f"  出力: {', '.join(self.output_names)}")
            print(f"  プロバイダー: {self.session.get_providers()}")

        except Exception as e:
            raise RuntimeError(f"BlazeFaceモデルの読み込みに失敗しました: {e}")

    def detect(self, img_bgr: np.ndarray) -> Tuple[bool, int, float]:
        """
        画像から顔を検出

        Args:
            img_bgr: OpenCV BGR画像（任意サイズ）

        Returns:
            (検出されたか, 検出数, 最大信頼度スコア)
        """
        boxes, scores = self._run_inference(img_bgr)

        count = len(scores)
        detected = count > 0
        max_score = float(np.max(scores)) if count > 0 else 0.0

        return detected, count, max_score

    def _preprocess(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        画像を前処理してモデル入力形式に変換

        Args:
            img_bgr: OpenCV BGR画像

        Returns:
            正規化済み入力テンソル (1, 3, 128, 128), 値域 0.0〜1.0
        """
        # BGR → RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # リサイズ
        img_resized = cv2.resize(img_rgb, self.input_size, interpolation=cv2.INTER_LINEAR)

        # 正規化（0〜255 → 0.0〜1.0）
        img_normalized = img_resized.astype(np.float32) / 255.0

        # HWC → CHW
        img_transposed = np.transpose(img_normalized, (2, 0, 1))

        # バッチ次元追加 (1, C, H, W)
        input_tensor = np.expand_dims(img_transposed, axis=0).astype(np.float32)

        return input_tensor

    def _run_inference(self, img_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        推論を実行し、(boxes, scores) を返す

        Returns:
            boxes:  (N, 16) 正規化座標 [top_y, top_x, bot_y, bot_x, ランドマーク6組]
            scores: (N,) 信頼度スコア。モデルの内蔵NMS/閾値処理により、
                    confidence_threshold以上のもののみが返る想定。
        """
        if self.session is None:
            raise RuntimeError("モデルがロードされていません。先にload()を呼んでください。")

        input_tensor = self._preprocess(img_bgr)

        feed = {
            self.input_name: input_tensor,
            "conf_threshold": np.array([self.confidence_threshold], dtype=np.float32),
            "max_detections": np.array([self.max_detections], dtype=np.int64),
            "iou_threshold": np.array([self.iou_threshold], dtype=np.float32),
        }
        # モデルが想定外の入力名しか持たない場合は image のみで再試行
        available_inputs = {inp.name for inp in self.session.get_inputs()}
        feed = {k: v for k, v in feed.items() if k in available_inputs}
        if self.input_name not in feed:
            feed[self.input_name] = input_tensor

        try:
            outs = self.session.run(self.output_names, feed)
        except Exception as e:
            print(f"推論エラー: {e}")
            return np.zeros((0, 16), dtype=np.float32), np.zeros((0,), dtype=np.float32)

        if len(outs) == 0:
            return np.zeros((0, 16), dtype=np.float32), np.zeros((0,), dtype=np.float32)

        boxes = outs[0]
        if boxes.ndim == 3:
            boxes = boxes[0]
        elif boxes.ndim == 1:
            boxes = boxes.reshape(-1, 16) if boxes.size % 16 == 0 else boxes.reshape(1, -1)

        if len(outs) > 1:
            scores = outs[1]
            if scores.ndim == 2:
                scores = scores[0]
        else:
            scores = np.ones(len(boxes), dtype=np.float32)

        # 念のためクライアント側でも閾値フィルタ
        if len(scores) > 0:
            keep = scores >= self.confidence_threshold
            boxes = boxes[keep]
            scores = scores[keep]

        return boxes, scores

    def detect_with_visualization(self, img_bgr: np.ndarray) -> Tuple[bool, int, float, np.ndarray]:
        """
        顔検出を実行し、検出結果を可視化した画像も返す

        Args:
            img_bgr: OpenCV BGR画像

        Returns:
            (検出されたか, 検出数, 最大信頼度スコア, 可視化画像)
        """
        boxes, scores = self._run_inference(img_bgr)

        count = len(scores)
        detected = count > 0
        max_score = float(np.max(scores)) if count > 0 else 0.0

        vis_img = img_bgr.copy()
        h, w = img_bgr.shape[:2]

        for bbox, score in zip(boxes, scores):
            top_y, top_x, bot_y, bot_x = bbox[0], bbox[1], bbox[2], bbox[3]

            x1 = int(top_x * w)
            y1 = int(top_y * h)
            x2 = int(bot_x * w)
            y2 = int(bot_y * h)

            if x2 - x1 < 2 or y2 - y1 < 2:
                continue

            cv2.rectangle(vis_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{score:.2f}"
            cv2.putText(vis_img, label, (x1, max(0, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # ランドマーク（目・鼻・口・頬）を描画
            landmark_pairs = bbox[4:16].reshape(-1, 2)
            for lx, ly in landmark_pairs:
                cx = int(lx * w)
                cy = int(ly * h)
                cv2.circle(vis_img, (cx, cy), 3, (0, 0, 255), -1)

        return detected, count, max_score, vis_img

    def unload(self):
        """モデルをアンロード（メモリ解放）"""
        if self.session is not None:
            self.session = None
            print("✓ BlazeFaceモデルをアンロードしました")


# ============================================================
# テスト・デバッグ用関数
# ============================================================

def test_blazeface_detector():
    """BlazeFaceDetectorのテスト"""
    import sys
    from pathlib import Path

    # モデルパス
    model_path = Path("image_orient_tool/resources/models/blazeface.onnx")

    if not model_path.exists():
        print(f"✗ モデルが見つかりません: {model_path}")
        print("  download_blazeface.pyを実行してください。")
        sys.exit(1)

    # 検出器を作成
    detector = BlazeFaceDetector(model_path, confidence_threshold=0.5)
    detector.load()

    # テスト画像を読み込み
    test_image_path = "test_image.jpg"  # テスト用の画像パス

    if not Path(test_image_path).exists():
        print(f"✗ テスト画像が見つかりません: {test_image_path}")
        print("  人物が写った画像を用意してください。")
        sys.exit(1)

    img = cv2.imread(test_image_path)

    # 顔検出実行
    detected, count, score, vis_img = detector.detect_with_visualization(img)

    print(f"\n=== 顔検出結果 ===")
    print(f"検出: {'✓ あり' if detected else '✗ なし'}")
    print(f"検出数: {count}人")
    print(f"最大スコア: {score:.3f}")

    # 結果を保存
    output_path = "test_output.jpg"
    cv2.imwrite(output_path, vis_img)
    print(f"\n可視化画像を保存しました: {output_path}")

    detector.unload()


if __name__ == "__main__":
    test_blazeface_detector()
