from PySide6.QtCore import QObject, Signal
from services.neural import VOICES

PREVIEW = 'Thank you for giving me this opportunity. I have experience in compliance, risk control, and international business.'


class Reader(QObject):
    changed = Signal()
    highlight = Signal(int)
    problem = Signal(str)

    def __init__(self, neural, audio):
        super().__init__()
        self.neural, self.audio = neural, audio
        self.sentences = []
        self.index = 0
        self.mode = 'Continuous'
        self.continuous = True
        self.voice = next(iter(VOICES))
        self.speed = .9
        self.offline = False
        self.state = 'idle'
        self.token = 0
        self.preview_snapshot = None
        self.resume_position = 0
        self.pending_path = None
        neural.ready.connect(self.ready)
        neural.failed.connect(self.failure)
        audio.finished.connect(self.finished)
        audio.failed.connect(self.failure)
        audio.started.connect(self.started)

    def cancel(self):
        self.token += 1
        self.neural.cancel()
        self.audio.stop()
        self.pending_path = None

    def stop(self):
        self.cancel()
        if self.preview_snapshot:
            self.index, self.continuous, _, _ = self.preview_snapshot
        self.preview_snapshot = None
        self.state = 'idle'
        self.changed.emit()

    def set_sentences(self, sentences):
        self.stop()
        self.sentences = sentences
        self.index = min(self.index, max(0, len(sentences)-1))

    def read(self, index, continuous=None):
        if not 0 <= index < len(self.sentences):
            return
        self.preview_snapshot = None
        self.cancel()
        self.index = index
        self.continuous = (self.mode == 'Continuous') if continuous is None else continuous
        self.resume_position = 0
        self.highlight.emit(index)
        self.generate(self.sentences[index].text)

    def generate(self, text):
        self.state = 'loading'
        self.changed.emit()
        if self.offline:
            self.audio.speak(self.token, text, self.speed)
        else:
            self.neural.request(self.token, text, self.voice, self.speed)

    def ready(self, token, path):
        if token != self.token or self.state not in ('loading', 'paused'):
            return
        if self.state == 'paused':
            self.pending_path = path
        else:
            self.audio.play(token, path, self.resume_position)

    def started(self, token):
        if token == self.token:
            self.state = 'playing'
            self.changed.emit()

    def finished(self, token):
        if token != self.token or self.state not in ('playing', 'loading'):
            return
        if self.preview_snapshot:
            self.restore_preview()
        elif self.continuous and self.index + 1 < len(self.sentences):
            self.read(self.index + 1, True)
        else:
            self.state = 'completed'
            self.changed.emit()

    def toggle(self):
        if self.state in ('playing', 'loading'):
            self.audio.pause()
            self.state = 'paused'
            self.changed.emit()
        elif self.state == 'paused':
            self.state = 'loading'
            if self.pending_path:
                path, self.pending_path = self.pending_path, None
                self.audio.play(self.token, path, self.resume_position)
            else:
                self.audio.resume()
            self.changed.emit()
        elif self.state == 'completed' and not self.continuous:
            self.read(self.index + 1, False)
        else:
            self.read(self.index)

    def preview(self):
        if self.preview_snapshot:
            self.restore_preview()
            return
        self.preview_snapshot = (self.index, self.continuous, self.state, self.audio.position())
        self.cancel()
        self.resume_position = 0
        self.generate(PREVIEW)

    def restore_preview(self):
        index, continuous, state, position = self.preview_snapshot
        self.cancel()
        self.preview_snapshot = None
        self.index, self.continuous = index, continuous
        if state in ('playing', 'loading', 'paused') and self.sentences:
            self.resume_position = position
            self.generate(self.sentences[index].text)
            if state == 'paused':
                self.audio.pause()
                self.state = 'paused'
        else:
            self.state = state
        self.changed.emit()

    def failure(self, token, message):
        if token != self.token:
            return
        self.state = 'error'
        self.changed.emit()
        self.problem.emit(message)

    def retry(self, offline=False):
        self.offline = offline
        self.cancel()
        self.generate(PREVIEW if self.preview_snapshot else self.sentences[self.index].text if self.sentences else PREVIEW)
