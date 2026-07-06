# image_orient_tool/core/batch_processor.py
from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject
from typing import List
from .models import ImageItem
from .orientation import detect_orientation_hybrid
from .face_detection import BlazeFaceDetector

class WorkerSignals(QObject):
    finished_one = Signal(int, ImageItem)
    error = Signal(int, str)
    all_finished = Signal()

class ImageProcessWorker(QRunnable):
    def __init__(self, index: int, item: ImageItem, detector=None):
        super().__init__()
        self.index = index
        self.item = item
        self.detector = detector
        self.signals = WorkerSignals()
        self.cancel_requested = False
    
    def run(self):
        if self.cancel_requested:
            return
        try:
            # 向き判定・回転はorientation.pyで実施済みと仮定
            # 顔検出のみ実行
            if self.detector:
                detected, count, score = self.detector.detect(self.item.image_array)
                self.item.face_detected = detected
                self.item.face_count = count
                self.item.face_score = score
            
            self.signals.finished_one.emit(self.index, self.item)
        except Exception as e:
            self.signals.error.emit(self.index, str(e))

class BatchProcessor:
    def __init__(self):
        self.pool = QThreadPool.globalInstance()
        self.workers = []
    
    def process_batch(self, items: List[ImageItem], detector, progress_callback):
        self.workers.clear()
        for i, item in enumerate(items):
            worker = ImageProcessWorker(i, item, detector)
            worker.signals.finished_one.connect(progress_callback)
            self.workers.append(worker)
            self.pool.start(worker)
    
    def cancel_all(self):
        for w in self.workers:
            w.cancel_requested = True