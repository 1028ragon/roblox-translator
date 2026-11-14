"""Azure 연결 없이 실행하는 녹음 및 자막 표시 테스트."""

import time
import wave

from .config import TARGET_RATE


class ListSink:
    """--record-test 용: 받은 소리를 메모리에 모읍니다."""

    def __init__(self):
        self.chunks = []

    def write(self, b):
        self.chunks.append(b)


def run_record_test():
    from .audio.capture import LoopbackCapture

    sink = ListSink()
    cap = LoopbackCapture(sink)
    print("5초 동안 녹음합니다. 지금 영상이나 음악 등 소리를 재생하세요...")
    try:
        time.sleep(5)
    finally:
        cap.close()
    if not sink.chunks:
        print("[실패] 소리가 잡히지 않았습니다. 재생 중인 소리가 있었는지 확인하세요.")
        return
    with wave.open("test.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TARGET_RATE)
        w.writeframes(b"".join(sink.chunks))
    print("저장 완료: test.wav  (재생해서 소리가 들리면 캡처 성공)")


def schedule_overlay_test(bridge):
    """Qt 이벤트 루프에서 예제 자막을 순서대로 표시합니다."""
    from PySide6.QtCore import QTimer

    print("자막 창 테스트 중... (Ctrl+C 로 종료)")
    QTimer.singleShot(500, lambda: bridge.text.emit("Hello, how are you?", "안녕, 잘 지내?", True))
    QTimer.singleShot(2500, lambda: bridge.text.emit("Let's go to the next map", "다음 맵으로 가자", True))
    QTimer.singleShot(4500, lambda: bridge.text.emit("Wait for me", "나 기다려줘", False))
