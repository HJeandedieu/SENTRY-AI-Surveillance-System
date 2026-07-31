# core/stream.py
import cv2
import threading
import logging
import time
from config import get_stream_source, STREAM_WIDTH, STREAM_HEIGHT

log = logging.getLogger("perceptra")


class VideoStream:
    def __init__(self):
        self._source  = get_stream_source()
        self._cap     = None
        self._frame   = None
        self._ret     = False
        self._lock    = threading.Lock()
        self._running = False
        self._thread  = None
        self.width    = STREAM_WIDTH
        self.height   = STREAM_HEIGHT
        self.fps      = 25.0

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        log.info(f"[stream] Started — source: {self._source}")
        return self

    def _capture_loop(self):
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                log.warning("[stream] Stream unavailable — retrying in 5s...")
                time.sleep(5)
                self._cap = cv2.VideoCapture(self._source)
                continue

            ret, frame = self._cap.read()
            if not ret:
                log.warning("[stream] Frame read failed — reconnecting...")
                self._cap.release()
                self._cap = cv2.VideoCapture(self._source)
                time.sleep(2)
                continue

            with self._lock:
                self._ret   = ret
                self._frame = frame

    def read(self):
        with self._lock:
            if self._frame is None:
                return False, None
            return self._ret, self._frame.copy()

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        log.info("[stream] Stopped.")