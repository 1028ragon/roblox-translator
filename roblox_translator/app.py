"""실행 옵션을 해석하고 오디오, 번역, 자막 화면을 연결합니다."""

import argparse
from contextlib import ExitStack
import signal
import sys

from .config import SOURCE_LANG, TARGET_LANG, TARGET_RATE
from .credentials import load_credentials


def main():
    parser = argparse.ArgumentParser(description="로블록스 음성 채팅 실시간 번역 자막")
    parser.add_argument("--test-overlay", action="store_true", help="자막 창만 테스트")
    parser.add_argument("--record-test", action="store_true", help="5초 녹음 테스트")
    args = parser.parse_args()

    if args.record_test:
        from .diagnostics import run_record_test

        run_record_test()
        return 0

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from .ui.overlay import Bridge, Overlay

    app = QApplication(sys.argv)
    overlay = Overlay()
    bridge = Bridge()
    bridge.text.connect(overlay.on_text)

    # Qt 이벤트 루프에서도 Ctrl+C를 처리할 수 있게 합니다.
    signal.signal(signal.SIGINT, lambda *a: app.quit())
    keepalive = QTimer()
    keepalive.timeout.connect(lambda: None)
    keepalive.start(200)

    if args.test_overlay:
        from .diagnostics import schedule_overlay_test

        schedule_overlay_test(bridge)
        return app.exec()

    import azure.cognitiveservices.speech as speechsdk

    from .audio.capture import LoopbackCapture
    from .translation.azure import build_recognizer

    key, region = load_credentials()
    # 시작 도중 실패해도 생성된 자원을 역순으로 정리합니다.
    with ExitStack() as resources:
        push_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=speechsdk.audio.AudioStreamFormat(
                samples_per_second=TARGET_RATE, bits_per_sample=16, channels=1
            )
        )
        resources.callback(push_stream.close)
        recognizer = build_recognizer(
            speechsdk, key, region, push_stream, bridge.text.emit
        )
        resources.callback(
            lambda: recognizer.stop_continuous_recognition_async().get()
        )
        recognizer.start_continuous_recognition_async().get()
        capture = LoopbackCapture(push_stream)
        resources.callback(capture.close)
        print(f"실행 중: {SOURCE_LANG} -> {TARGET_LANG}  (종료: Ctrl+C)")
        return app.exec()
