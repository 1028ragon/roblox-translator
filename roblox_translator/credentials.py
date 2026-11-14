"""프로젝트 루트의 .env 또는 환경 변수에서 Azure 인증 정보를 읽습니다."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_credentials():
    """main.py와 같은 폴더의 .env 파일에서 키와 지역을 읽습니다."""
    values = {}
    env_path = PROJECT_ROOT / ".env"
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    key = values.get("AZURE_SPEECH_KEY") or os.environ.get("AZURE_SPEECH_KEY")
    region = values.get("AZURE_SPEECH_REGION") or os.environ.get("AZURE_SPEECH_REGION")
    if not key or not region:
        print("[오류] Azure 키가 없습니다.")
        print("  1) .env.example 파일을 복사해서 이름을 .env 로 바꾸세요.")
        print("  2) AZURE_SPEECH_KEY 와 AZURE_SPEECH_REGION 값을 채우세요.")
        sys.exit(1)
    return key, region
