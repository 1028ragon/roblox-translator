"""WASAPI 루프백 소리를 번역용 PCM 데이터로 변환합니다."""

import math

import numpy as np
from scipy.signal import resample_poly

from ..config import TARGET_RATE


class LoopbackCapture:
    """기본 스피커로 나가는 소리를 16kHz / 16bit / 모노로 바꿔 sink.write()로 보냅니다."""

    def __init__(self, sink):
        import pyaudiowpatch as pyaudio  # Windows 전용 라이브러리

        self._pyaudio = pyaudio
        self.sink = sink
        self.p = pyaudio.PyAudio()
        info = self._find_loopback_device()
        self.channels = int(info["maxInputChannels"])
        self.rate = int(info["defaultSampleRate"])
        g = math.gcd(TARGET_RATE, self.rate)
        self.up = TARGET_RATE // g
        self.down = self.rate // g
        print(f"[캡처] 장치: {info['name']} / {self.rate}Hz / {self.channels}채널")
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=info["index"],
            frames_per_buffer=int(self.rate * 0.1),
            stream_callback=self._callback,
        )

    def _find_loopback_device(self):
        pyaudio = self._pyaudio
        wasapi = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        speakers = self.p.get_device_info_by_index(wasapi["defaultOutputDevice"])
        if speakers.get("isLoopbackDevice"):
            return speakers
        for loopback in self.p.get_loopback_device_info_generator():
            if speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError("루프백 장치를 찾지 못했습니다. 기본 출력 장치를 확인하세요.")

    def _callback(self, in_data, frame_count, time_info, status):
        data = np.frombuffer(in_data, dtype=np.int16)
        if self.channels > 1:
            data = data.reshape(-1, self.channels).mean(axis=1)
        data = resample_poly(data.astype(np.float32), self.up, self.down)
        out = np.clip(data, -32768, 32767).astype(np.int16).tobytes()
        try:
            self.sink.write(out)
        except Exception as e:  # 종료 중 오류는 무시
            print("[캡처] 전송 오류:", e)
        return (None, self._pyaudio.paContinue)

    def close(self):
        try:
            self.stream.stop_stream()
            self.stream.close()
        finally:
            self.p.terminate()
