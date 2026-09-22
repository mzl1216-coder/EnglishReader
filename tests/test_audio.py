import io
import struct
import wave

from services.audio import Audio
from services.preroll import guarded_wave, RATE, LEAD_MS


def test_preroll_preserves_every_speech_sample_and_resume_offset():
    pcm = b''.join(struct.pack('<h', i % 30000 + 1) for i in range(RATE * 2))
    for position in (0, 381, 1700):
        data, offset = guarded_wave(pcm, position)
        with wave.open(io.BytesIO(data)) as wav:
            assert wav.getframerate() == RATE
            assert wav.readframes(RATE * LEAD_MS // 1000) == bytes(RATE * LEAD_MS // 1000 * 2)
            assert wav.readframes(RATE * 2) == pcm[position * RATE // 1000 * 2:]
        assert offset == position


def test_real_decode_pause_resume_and_cancel(qtbot, tmp_path):
    # Exercise Qt's decoder and source-device playback without network or speech.
    source = tmp_path / 'tone.wav'
    pcm = struct.pack('<h', 100) * (RATE * 2)
    with wave.open(str(source), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(pcm)
    audio = Audio()
    if not audio.device_available:
        import pytest
        pytest.skip('No Windows audio endpoint available')
    errors, starts, ends = [], [], []
    audio.failed.connect(lambda *args: errors.append(args))
    audio.started.connect(starts.append)
    audio.finished.connect(ends.append)
    try:
        audio.play(1, str(source))
        audio.pause()  # Pause while decoding must not start playback.
        qtbot.waitUntil(lambda: audio.player is not None, timeout=5000)
        assert audio.pcm == pcm
        assert not starts
        audio.resume()
        qtbot.waitUntil(lambda: starts == [1], timeout=5000)
        assert audio.position() == 0
        qtbot.waitUntil(lambda: audio.position() >= 250, timeout=5000)
        audio.pause()
        position = audio.position()
        audio.resume()
        assert abs(audio.position() - position) <= 1
        qtbot.waitUntil(lambda: ends == [1], timeout=7000)
        audio.play(2, str(source))
        audio.stop()  # Cancel before decoder completion.
        qtbot.wait(100)
        assert audio.player is None and audio.decoder is None
        assert 2 not in starts and 2 not in ends
        assert not errors
    finally:
        audio.stop()
