import io
import struct
import wave
import time
import pytest

from services.audio import Audio
from services.preroll import guarded_wave, RATE, LEAD_MS, WARM_LEAD_MS, WARM_IDLE_SECONDS


@pytest.mark.parametrize('lead_ms', [LEAD_MS, WARM_LEAD_MS])
def test_preroll_preserves_every_speech_sample_and_resume_offset(lead_ms):
    pcm = b''.join(struct.pack('<h', i % 30000 + 1) for i in range(RATE * 2))
    for position in (0, 381, 1700):
        data, offset = guarded_wave(pcm, position, lead_ms)
        with wave.open(io.BytesIO(data)) as wav:
            assert wav.getframerate() == RATE
            assert wav.readframes(RATE * lead_ms // 1000) == bytes(RATE * lead_ms // 1000 * 2)
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
        assert audio.lead_ms == LEAD_MS  # Decoding alone has not warmed the device.
        qtbot.waitUntil(lambda: starts == [1], timeout=5000)
        assert audio.position() == 0
        qtbot.waitUntil(lambda: audio.position() >= 250, timeout=5000)
        audio.pause()
        position = audio.position()
        audio.resume()
        assert audio.lead_ms == WARM_LEAD_MS
        assert abs(audio.position() - position) <= 1
        qtbot.waitUntil(lambda: ends == [1], timeout=7000)
        audio.play(2, str(source))
        qtbot.waitUntil(lambda: audio.player is not None, timeout=5000)
        assert audio.lead_ms == WARM_LEAD_MS  # Next sentence keeps the short gap.
        audio.pause()
        position = audio.position()
        audio.last_active = time.monotonic() - WARM_IDLE_SECONDS - 1
        audio.resume()
        assert audio.lead_ms == LEAD_MS  # A long pause restores onset protection.
        assert abs(audio.position() - position) <= 1
        audio.stop()
        audio.play(3, str(source))
        audio.stop()  # Cancel before decoder completion.
        qtbot.wait(100)
        assert audio.player is None and audio.decoder is None
        assert 3 not in starts and 3 not in ends
        assert not errors
    finally:
        audio.stop()


def test_idle_cancellation_does_not_extend_warm_window_and_device_loss_resets_it(qtbot):
    audio = Audio()
    previous = time.monotonic() - WARM_IDLE_SECONDS - 1
    audio.last_active = previous
    audio.stop()
    audio.stop()
    assert audio.last_active == previous
    audio.set_device('missing-headphones')
    assert audio.last_active is None
    audio.stop()
