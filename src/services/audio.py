import logging
from PySide6.QtCore import QObject, Signal, QUrl, QLocale, QBuffer, QIODevice
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaDevices, QAudioDevice, QAudioDecoder, QAudioFormat
from PySide6.QtTextToSpeech import QTextToSpeech
from services.preroll import guarded_wave, RATE, LEAD_MS


class Audio(QObject):
    finished = Signal(int)
    failed = Signal(int, str)
    started = Signal(int)
    devices_changed = Signal()

    def __init__(self):
        super().__init__()
        self.player = None
        self.speech = None
        self.decoder = None
        self.buffer = None
        self.pcm = None
        self.source_offset = 0
        self.active_token = None
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
        if self.device_available and self.output.device().id() != device.id():
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
        self.active_token = token
        self.source_offset = position
        decoder = QAudioDecoder(self)
        self.decoder = decoder
        fmt = QAudioFormat()
        fmt.setSampleRate(RATE)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        decoder.setAudioFormat(fmt)
        chunks = bytearray()

        def collect():
            if decoder is self.decoder:
                buffer = decoder.read()
                if buffer.isValid():
                    chunks.extend(bytes(buffer.constData()))

        def decoded():
            if decoder is not self.decoder:
                return
            self.decoder = None
            decoder.deleteLater()
            self.pcm = bytes(chunks)
            if not self.pcm:
                self.failed.emit(token, 'Audio playback failed: empty decoded speech.')
                return
            self._play_pcm(token, position)

        def decode_failed(error):
            if decoder is self.decoder:
                message = decoder.errorString()
                self.stop()
                self.failed.emit(token, 'Audio playback failed: ' + message)

        decoder.bufferReady.connect(collect)
        decoder.finished.connect(decoded)
        decoder.error.connect(decode_failed)
        decoder.setSource(QUrl.fromLocalFile(path))
        decoder.start()

    def _play_pcm(self, token, position):
        wav, self.source_offset = guarded_wave(self.pcm, position)
        buffer = QBuffer(self)
        buffer.setData(wav)
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.buffer = buffer
        player = QMediaPlayer(self)
        self.player = player
        player.setAudioOutput(self.output)
        def status(value):
            if player is not self.player:
                return
            if value == QMediaPlayer.MediaStatus.LoadedMedia:
                if not self.paused:
                    player.play()
            elif value == QMediaPlayer.MediaStatus.EndOfMedia:
                self.finished.emit(token)
        player.mediaStatusChanged.connect(status)
        player.playbackStateChanged.connect(lambda s: self.started.emit(token) if player is self.player and not self.paused and s == QMediaPlayer.PlaybackState.PlayingState else None)
        def failed(error, message):
            if player is self.player:
                logging.error('Audio playback failed: %s', message)
                self.failed.emit(token, 'Audio playback failed: ' + message)
        player.errorOccurred.connect(failed)
        logging.info('Playing audio on %s', self.output_name())
        # Silence is part of the SAME stream as speech, not a delay before opening it.
        player.setSourceDevice(buffer, QUrl('speech.wav'))

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
            position = self.position()
            self._stop_player()
            self._play_pcm(self.active_token, position)
        if self.speech:
            self.speech.resume()

    def position(self):
        return self.source_offset + max(0, self.player.position() - LEAD_MS) if self.player else self.source_offset

    def _stop_player(self):
        player, buffer = self.player, self.buffer
        self.player = self.buffer = None
        if player:
            player.stop()
            player.setSource(QUrl())
            player.setAudioOutput(None)
            player.deleteLater()
        if buffer:
            buffer.close()
            buffer.deleteLater()

    def stop(self):
        self._stop_player()
        decoder, speech = self.decoder, self.speech
        self.decoder = self.speech = None
        self.pcm = None
        self.source_offset = 0
        self.active_token = None
        if decoder:
            decoder.stop()
            decoder.deleteLater()
        if speech:
            speech.stop(QTextToSpeech.BoundaryHint.Immediate)
            speech.deleteLater()
