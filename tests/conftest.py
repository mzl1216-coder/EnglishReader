import pytest
from PySide6.QtCore import QObject, Signal


class FakeNeural(QObject):
    ready = Signal(int, str)
    failed = Signal(int, str)
    voices = Signal(list)

    def __init__(self):
        super().__init__()
        self.requests = []
        self.cancelled = 0

    def request(self, *args):
        self.requests.append(args)

    def cancel(self):
        self.cancelled += 1

    def close(self):
        pass


class FakeAudio(QObject):
    finished = Signal(int)
    started = Signal(int)
    failed = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.plays = []
        self.paused = False
        self.token = 0

    def play(self, token, path, position=0):
        self.token = token
        self.plays.append((token, path, position))
        self.started.emit(token)

    def speak(self, token, text, speed):
        self.play(token, text)

    def stop(self):
        pass

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.started.emit(self.token)

    def position(self):
        return 1234


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    monkeypatch.setenv('ENGLISHREADER_DATA_DIR', str(tmp_path))
    from ui.window import ReaderWindow
    w = ReaderWindow(FakeNeural(), FakeAudio())
    if w.mini:
        w.toggle_mini()
    qtbot.addWidget(w)
    w.show()
    w.text.setPlainText('\n\n'.join(f'This is sentence number {i}, for English listening practice.' for i in range(1, 21)))
    yield w
    w.close()
