import asyncio
import hashlib
import logging
import threading
import time
from PySide6.QtCore import QObject, Signal
import edge_tts
from utils.storage import directories

VOICES = {
    'en-US-AndrewMultilingualNeural': 'American English - Andrew · Formal / Natural',
    'en-US-AriaNeural': 'American English - Aria · Formal / Broadcast',
    'en-US-AvaMultilingualNeural': 'American English - Ava · Natural / Conversational',
    'en-US-BrianMultilingualNeural': 'American English - Brian · Natural / Conversational',
}


class NeuralService(QObject):
    ready = Signal(int, str)
    failed = Signal(int, str)
    voices = Signal(list)

    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.pending = None
        self.cache = directories()[1] / 'cache'
        asyncio.run_coroutine_threadsafe(self.trim_cache(), self.loop)
        self.catalog = asyncio.run_coroutine_threadsafe(self.list_voices(), self.loop)

    async def trim_cache(self):
        """Keep at most 300 MB / 30 days of generated audio, best effort."""
        try:
            files = sorted(self.cache.glob('*.mp3'), key=lambda p: p.stat().st_mtime, reverse=True)
            total = 0
            for file in files:
                stat = file.stat()
                total += stat.st_size
                if total > 300_000_000 or time.time() - stat.st_mtime > 30 * 86400:
                    try:
                        file.unlink()
                    except OSError:
                        pass
        except OSError:
            logging.exception('Cache cleanup skipped')

    async def list_voices(self):
        try:
            voices = await asyncio.wait_for(edge_tts.list_voices(), 20)
            self.voices.emit([v['ShortName'] for v in voices if v['Locale'] == 'en-US' and 'Neural' in v['ShortName']])
        except Exception:
            logging.exception('Voice discovery unavailable; retaining preferred voices')

    def request(self, token, text, voice, speed):
        self.cancel()
        self.pending = asyncio.run_coroutine_threadsafe(self.generate(token, text, voice, speed), self.loop)

    async def generate(self, token, text, voice, speed):
        key = hashlib.sha256(f'{voice}|{speed}|{text}'.encode()).hexdigest()
        target = self.cache / (key + '.mp3')
        temporary = self.cache / f'{key}.{token}.part'
        try:
            if not target.exists() or not target.stat().st_size:
                await asyncio.wait_for(edge_tts.Communicate(text, voice, rate=f'{round((speed-1)*100):+d}%', pitch='+0Hz', volume='+0%').save(str(temporary)), 35)
                temporary.replace(target)
            self.ready.emit(token, str(target))
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logging.exception('Neural synthesis failed')
            self.failed.emit(token, str(exc))
        finally:
            temporary.unlink(missing_ok=True)

    def cancel(self):
        if self.pending:
            self.pending.cancel()

    def close(self):
        self.cancel()
        self.catalog.cancel()
        async def cleanup():
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        try:
            asyncio.run_coroutine_threadsafe(cleanup(), self.loop).result(timeout=3)
        except Exception:
            logging.exception('Worker shutdown')
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=3)
        if not self.thread.is_alive():
            self.loop.close()
