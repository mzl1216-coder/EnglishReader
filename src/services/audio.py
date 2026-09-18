from PySide6.QtCore import QObject, Signal, QUrl, QLocale
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtTextToSpeech import QTextToSpeech


class Audio(QObject):
    finished = Signal(int)
    failed = Signal(int, str)
    started = Signal(int)

    def __init__(self):
        super().__init__()
        self.player = None
        self.speech = None
        self.output = QAudioOutput(self)
        self.output.setVolume(1)
        self.paused = False

    def play(self, token, path, position=0):
        self.stop()
        self.paused = False
        player = QMediaPlayer(self)
        self.player = player
        player.setAudioOutput(self.output)
        def status(value):
            if player is not self.player:
                return
            if value == QMediaPlayer.MediaStatus.LoadedMedia:
                if position:
                    player.setPosition(position)
                if not self.paused:
                    player.play()
            elif value == QMediaPlayer.MediaStatus.EndOfMedia:
                self.finished.emit(token)
        player.mediaStatusChanged.connect(status)
        player.playbackStateChanged.connect(lambda s: self.started.emit(token) if s == QMediaPlayer.PlaybackState.PlayingState else None)
        player.errorOccurred.connect(lambda e, message: self.failed.emit(token, message))
        player.setSource(QUrl.fromLocalFile(path))

    def speak(self, token, text, speed):
        self.stop()
        speech = QTextToSpeech('sapi', self)
        self.speech = speech
        speech.setLocale(QLocale('en_US'))
        voices = [v for v in speech.availableVoices() if v.locale().name() == 'en_US']
        if not voices:
            self.failed.emit(token, 'No offline US English voice is installed. Add an English (United States) speech voice in Windows Settings.')
            return
        speech.setLocale(QLocale('en_US'))
        speech.setVoice(voices[0])
        speech.setRate(max(-1.0, min(1.0, speed - 1)))
        speech.setVolume(1)
        spoken = [False]
        def state(value):
            if speech is not self.speech:
                return
            if value == QTextToSpeech.State.Speaking:
                spoken[0] = True
                self.started.emit(token)
            elif value == QTextToSpeech.State.Ready and spoken[0]:
                self.finished.emit(token)
            elif value == QTextToSpeech.State.Error:
                self.failed.emit(token, speech.errorString())
        speech.stateChanged.connect(state)
        speech.say(text)

    def pause(self):
        self.paused = True
        if self.player:
            self.player.pause()
        if self.speech:
            self.speech.pause(QTextToSpeech.BoundaryHint.Immediate)

    def resume(self):
        self.paused = False
        if self.player:
            self.player.play()
        if self.speech:
            self.speech.resume()

    def position(self):
        return self.player.position() if self.player else 0

    def stop(self):
        player, speech = self.player, self.speech
        self.player = self.speech = None
        if player:
            player.stop()
            player.deleteLater()
        if speech:
            speech.stop(QTextToSpeech.BoundaryHint.Immediate)
            speech.deleteLater()
