"""Azure Speech 번역 결과를 on_text(원문, 번역문, 확정 여부)로 전달합니다."""

from ..config import SOURCE_LANG, TARGET_LANG


def build_recognizer(speechsdk, key, region, push_stream, on_text):
    cfg = speechsdk.translation.SpeechTranslationConfig(subscription=key, region=region)
    cfg.speech_recognition_language = SOURCE_LANG
    cfg.add_target_language(TARGET_LANG)
    audio_cfg = speechsdk.audio.AudioConfig(stream=push_stream)
    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=cfg, audio_config=audio_cfg
    )

    def on_recognizing(evt):  # 말하는 도중 (임시 결과)
        tr = evt.result.translations.get(TARGET_LANG, "")
        if tr:
            on_text(evt.result.text, tr, False)

    def on_recognized(evt):  # 한 문장 확정
        r = evt.result
        if r.reason == speechsdk.ResultReason.TranslatedSpeech and r.text:
            tr = r.translations.get(TARGET_LANG, "")
            print(f"[{SOURCE_LANG}] {r.text}\n[{TARGET_LANG}] {tr}\n")
            on_text(r.text, tr, True)

    def on_canceled(evt):
        print("[Azure] 중단됨:", evt.reason, getattr(evt, "error_details", ""))
        print("        키/지역이 맞는지, 인터넷이 연결됐는지 확인하세요.")

    recognizer.recognizing.connect(on_recognizing)
    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    return recognizer
