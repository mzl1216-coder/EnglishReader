import logging
from PySide6.QtCore import QObject, Signal, QUrl, QLocale
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaDevices, QAudioDevice
from PySide6.QtTextToSpeech import QTextToSpeech


class Audio(QObject):
    finished = Signal(int)
    failed = Signal(int, str)
    started = Signal(int)
    devices_changed = Signal()

    def __init__(self):
        super().__init__()
        self.player = None
        self.speech = None
        self.output = QAudioOutput(self)
        self.output.setVolume(1)
        self.paused = False
        self.device_id = ''
        self.devices = QMediaDevices(self)
        self.devices.audioOutputsChanged.connect(self.refresh_device)
        self.refresh_device()

    def available_outputs(self):
        return [(bytes(d.id().toBase64()).decode(), d.description()) for d in QMediaDevices.audioOutputs()]

    def set_device(self, device_id):
        self.device_id = device_id or ''
        self.refresh_device()

    def refresh_device(self):
        device = next((d for d in QMediaDevices.audioOutputs() if bytes(d.id().toBase64()).decode() == self.device_id), QAudioDevice()) if self.device_id else QMediaDevices.defaultAudioOutput()
        self.device_available = not device.isNull()
        if self.device_available:
            self.output.setDevice(device)
        self.output.setMuted(not self.device_available)
        logging.info('Audio output: %s; unavailable=%s', device.description(), device.isNull())
        self.devices_changed.emit()

    def output_name(self):
        return self.output.device().description() if self.device_available else 'Audio device unavailable'

    def play(self, token, path, position=0):
        self.stop()
        self.paused = False
        self.refresh_device()
        if not self.device_available:
            self.failed.emit(token, 'Audio output unavailable. Connect speakers or headphones, then retry.')
            return
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
        def failed(error, message):
            if player is self.player:
                logging.error('Audio playback failed: %s', message)
                self.failed.emit(token, 'Audio playback failed: ' + message)
        player.errorOccurred.connect(failed)
        logging.info('Playing audio on %s', self.output_name())
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
            player.setAudioOutput(None)
            player.deleteLater()
        if speech:
            speech.stop(QTextToSpeech.BoundaryHint.Immediate)
            speech.deleteLater()
