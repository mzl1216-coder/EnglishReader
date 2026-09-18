"""Opt-in integration verification: real Edge service, MP3 playback and SAPI."""
import asyncio
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
OUT = ROOT / 'test-results' / 'runtime'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['ENGLISHREADER_DATA_DIR'] = str(OUT)
import edge_tts
from services.neural import VOICES


async def synthesis():
    available = await asyncio.wait_for(edge_tts.list_voices(), 30)
    names = {v['ShortName'] for v in available if v['Locale'] == 'en-US'}
    result = {'available_us_voices': len(names), 'voices': {}}
    for voice in VOICES:
        if voice not in names:
            result['voices'][voice] = 'not available'
            continue
        path = OUT / f'{voice}.mp3'
        await asyncio.wait_for(edge_tts.Communicate('Thank you for giving me this opportunity.', voice, rate='-10%').save(str(path)), 45)
        assert path.stat().st_size > 1000
        result['voices'][voice] = path.stat().st_size
    return result


def playback(result):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication
    from services.audio import Audio
    app = QApplication([])
    audio = Audio()
    for kind in ('neural', 'offline'):
        loop = QEventLoop()
        outcome = []
        def done(token):
            outcome.append('finished')
            loop.quit()
        def failed(token, message):
            outcome.append(message)
            loop.quit()
        audio.finished.connect(done)
        audio.failed.connect(failed)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(30000)
        if kind == 'neural':
            path = next(OUT.glob('*.mp3'))
            audio.play(1, str(path))
        else:
            audio.speak(2, 'This is the offline Windows voice.', .9)
        if not outcome:
            loop.exec()
        audio.stop()
        timer.stop()
        audio.finished.disconnect(done)
        audio.failed.disconnect(failed)
        result[kind + '_playback'] = outcome or ['timeout']
        app.processEvents()
    result['passed'] = all(result[k] == ['finished'] for k in ('neural_playback', 'offline_playback'))


if __name__ == '__main__':
    result = asyncio.run(synthesis())
    playback(result)
    (OUT / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
