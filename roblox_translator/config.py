"""번역 언어, 자막 표시 및 오디오 설정."""

SOURCE_LANG = "en-US"   # 상대가 말하는 언어. 예: en-US, ja-JP, zh-CN, ru-RU, es-ES
TARGET_LANG = "ko"      # 자막으로 보고 싶은 언어. 예: ko, en, ja
SHOW_ORIGINAL = True    # 원문도 작게 같이 보여줄지
MAX_LINES = 3           # 화면에 동시에 보일 최대 줄 수
LINE_TTL_SEC = 6        # 확정된 자막이 화면에 남는 시간(초)
FONT_SIZE_PX = 26       # 글자 크기
BOTTOM_MARGIN_PX = 90   # 화면 아래쪽 여백

TARGET_RATE = 16000     # Azure에 보낼 샘플레이트 (바꾸지 마세요)
