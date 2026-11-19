# 로블록스 음성 채팅 번역 자막 (프로토타입)

PC 스피커 소리 → WASAPI 루프백 캡처 → Azure 음성 인식·번역 → 자막 오버레이 순서로 동작합니다.

이슈, 브랜치, 커밋, PR 작성 규칙은 [Git Convention](git%20convention.md)을 참고하세요.

제품 목표, 단계별 출시 범위와 기능 요구사항은 [PRD](docs/PRD.md)를 참고하세요.

GitHub에 등록할 전체 이슈 제목·본문과 선행 작업은 [이슈 등록 초안](docs/ISSUES.md)에 정리되어 있습니다.

## 프로젝트 구조

```text
roblox-translator/
├── main.py                     # 프로그램 실행 진입점
├── roblox_translator/
│   ├── app.py                  # 실행 옵션, 기능 연결, 시작·종료 처리
│   ├── config.py               # 번역 언어, 자막 모양, 오디오 설정
│   ├── credentials.py          # Azure 키와 지역 읽기
│   ├── diagnostics.py          # 녹음 및 자막 표시 테스트
│   ├── audio/
│   │   └── capture.py          # 스피커 캡처, 모노 변환, 리샘플링
│   ├── translation/
│   │   └── azure.py            # Azure 음성 인식·번역 및 결과 전달
│   └── ui/
│       └── overlay.py          # 자막 창, 표시 시간, GUI 스레드 신호
├── tests/                      # 설정 로딩 및 번역 결과 전달 회귀 테스트
├── .env.example
├── .env                        # 직접 생성하는 Azure 인증 정보
└── requirements.txt
```

언어와 자막 모양은 `roblox_translator/config.py`에서 변경합니다.
`.env`는 기존처럼 `main.py`와 같은 폴더에 두며, 실행 위치와 관계없이 이 파일을 읽습니다.
`.env`에 값이 없으면 시스템의 `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` 환경 변수를 사용합니다.

오디오 캡처는 `write(bytes)`를 제공하는 대상에 PCM 데이터를 전달합니다.
번역 모듈은 `on_text(원문, 번역문, 확정 여부)` 콜백으로 결과를 전달하고,
`app.py`가 이를 자막 창의 Qt 신호에 연결합니다.
로블록스 전용 캡처나 다른 번역 서비스를 추가할 때 각 모듈을 따로 수정할 수 있습니다.

## 1. 설치 (한 번만)
1. Python 3.11 설치 (설치 화면에서 "Add Python to PATH" 체크)
2. 이 폴더를 PyCharm에서 프로젝트로 열기 (가상환경 .venv 자동 생성)
3. PyCharm 아래쪽 Terminal 탭에서:
   pip install -r requirements.txt

## 2. 단계별 테스트 (순서대로!)
1. 자막 창 테스트 (Azure 필요 없음)
   python main.py --test-overlay
   -> 화면 아래에 자막 3개가 차례로 뜨면 성공 (Ctrl+C로 종료)
2. 소리 캡처 테스트 (Azure 필요 없음)
   유튜브 등으로 소리를 틀어 둔 채로:
   python main.py --record-test
   -> test.wav 가 생기고, 재생했을 때 소리가 들리면 성공
3. Azure 키 넣기
   .env.example 을 복사해서 .env 로 이름을 바꾸고 키/지역 입력
4. 본 실행
   python main.py
   -> 영어 영상 등을 틀어서 한국어 자막이 뜨는지 확인

## 3. 로블록스와 같이 쓰기
- 로블록스를 "창모드" 또는 "테두리 없는 창모드"로 실행 (전체화면 독점이면 자막이 안 보임)
- 상대 언어가 영어가 아니면 roblox_translator/config.py의 SOURCE_LANG 을 바꾸기 (ja-JP, zh-CN 등)
- 자막 창은 클릭이 통과되어서 마우스로 닫을 수 없음 -> 터미널에서 Ctrl+C 또는 PyCharm 정지 버튼

## 알려진 한계
- 시스템 전체 소리를 잡기 때문에 게임 효과음, 다른 소리도 섞임 (나중에 로블록스만 캡처하도록 개선 가능)
- 여러 사람이 동시에 말하면 누가 말했는지 구분 못 함
- 상대 언어는 한 번에 한 가지만 지정 (자동 감지는 다음 단계)
- 소리가 아예 안 나올 때는 데이터가 안 들어오는 게 정상

## 코드 검증

프로젝트 폴더에서 다음 명령으로 회귀 테스트를 실행합니다. Azure 연결이나 오디오 장치는 필요 없습니다.

```powershell
python -m unittest discover -s tests -v
```
