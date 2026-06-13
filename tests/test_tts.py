"""TTS provider: stub behaviour and factory selection."""
from tests._bootstrap import Base

from ph.providers import get_tts
from ph.providers.tts import StubTTS


class TestTTS(Base):
    def test_factory_returns_stub_without_provider(self):
        tts = get_tts()
        self.assertIsInstance(tts, StubTTS)

    def test_stub_returns_empty_bytes(self):
        # Empty bytes means "skip the voice reply" — adapter must not send audio.
        out = StubTTS().synthesize("Hello Maria, let's fix your wifi.", "en")
        self.assertIsInstance(out, bytes)
        self.assertEqual(out, b"")
