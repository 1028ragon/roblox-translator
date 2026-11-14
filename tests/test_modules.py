"""파일 분리 후 인증 정보와 번역 결과 전달 동작을 검증합니다."""

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from roblox_translator import credentials
from roblox_translator.config import SOURCE_LANG, TARGET_LANG
from roblox_translator.translation.azure import build_recognizer


class CredentialsTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(directory)
        self.enterContext(patch.object(credentials, "PROJECT_ROOT", self.root))
        self.enterContext(patch.dict(os.environ, {}, clear=True))

    def test_env_file_takes_priority_over_environment(self):
        (self.root / ".env").write_text(
            '# comment\nAZURE_SPEECH_KEY="file-key"\n'
            "AZURE_SPEECH_REGION='file-region'\ninvalid-line\n",
            encoding="utf-8",
        )
        os.environ.update(AZURE_SPEECH_KEY="env-key", AZURE_SPEECH_REGION="env-region")
        self.assertEqual(credentials.load_credentials(), ("file-key", "file-region"))

    def test_environment_without_env_file(self):
        os.environ.update(AZURE_SPEECH_KEY="env-key", AZURE_SPEECH_REGION="env-region")
        self.assertEqual(credentials.load_credentials(), ("env-key", "env-region"))

    def test_missing_region_exits_with_error(self):
        os.environ["AZURE_SPEECH_KEY"] = "env-key"
        with patch("builtins.print"), self.assertRaises(SystemExit) as error:
            credentials.load_credentials()
        self.assertEqual(error.exception.code, 1)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.sdk = MagicMock()
        self.stream = object()
        self.on_text = MagicMock()
        self.recognizer = build_recognizer(
            self.sdk, "key", "region", self.stream, self.on_text
        )

    def event(self, text="Hello", translations=None, reason=None):
        return SimpleNamespace(result=SimpleNamespace(
            text=text,
            translations=translations if translations is not None else {TARGET_LANG: "안녕"},
            reason=reason,
        ))

    def test_config_and_partial_result(self):
        config = self.sdk.translation.SpeechTranslationConfig.return_value
        self.assertEqual(config.speech_recognition_language, SOURCE_LANG)
        config.add_target_language.assert_called_once_with(TARGET_LANG)
        self.sdk.audio.AudioConfig.assert_called_once_with(stream=self.stream)
        callback = self.recognizer.recognizing.connect.call_args.args[0]
        callback(self.event())
        self.on_text.assert_called_once_with("Hello", "안녕", False)

    def test_final_result(self):
        callback = self.recognizer.recognized.connect.call_args.args[0]
        with patch("builtins.print"):
            callback(self.event(reason=self.sdk.ResultReason.TranslatedSpeech))
        self.on_text.assert_called_once_with("Hello", "안녕", True)

    def test_empty_partial_and_non_translation_are_ignored(self):
        partial = self.recognizer.recognizing.connect.call_args.args[0]
        final = self.recognizer.recognized.connect.call_args.args[0]
        partial(self.event(translations={}))
        final(self.event(reason="no-match"))
        final(self.event(text="", reason=self.sdk.ResultReason.TranslatedSpeech))
        self.on_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
