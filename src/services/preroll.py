"""Protect speech onset while the Windows/headphone audio stream wakes up."""
import io
import wave

RATE = 24000
LEAD_MS = 750
WARM_LEAD_MS = 150
WARM_IDLE_SECONDS = 8


def guarded_wave(pcm, position=0, lead_ms=LEAD_MS):
    # Position is in the original speech, never in the added startup silence.
    frame = min(len(pcm) // 2, max(0, int(position * RATE / 1000)))
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(bytes(RATE * lead_ms // 1000 * 2) + pcm[frame * 2:])
    return output.getvalue(), frame * 1000 // RATE
