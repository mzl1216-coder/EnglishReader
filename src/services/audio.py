import logging
import time
from PySide6.QtCore import QObject, Signal, QUrl, QLocale, QBuffer, QIODevice
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaDevices, QAudioDevice, QAudioDecoder, QAudioFormat
from PySide6.QtTextToSpeech import QTextToSpeech
from services.preroll import guarded_wave, RATE, LEAD_MS, WARM_LEAD_MS, WARM_IDLE_SECONDS


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
        self.last_active = None
        self.lead_ms = LEAD_MS
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
        was_available = getattr(self, 'device_available', False)
        self.device_available = not device.isNull()
        if not self.device_available or not was_available or self.output.device().id() != device.id():
            self.last_active = None
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
        self.lead_ms = WARM_LEAD_MS if self.last_active is not None and time.monotonic() - self.last_active < WARM_IDLE_SECONDS else LEAD_MS
        wav, self.source_offset = guarded_wave(self.pcm, position, self.lead_ms)
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
                self.last_active = time.monotonic()
                self.finished.emit(token)
        player.mediaStatusChanged.connect(status)
        player.positionChanged.connect(lambda _: self._remember_activity() if player is self.player else None)
        player.playbackStateChanged.connect(lambda s: self.started.emit(token) if player is self.player and not self.paused and s == QMediaPlayer.PlaybackState.PlayingState else None)
        def failed(error, message):
            if player is self.player:
                logging.error('Audio playback failed: %s', message)
                self.failed.emit(token, 'Audio playback failed: ' + message)
        player.errorOccurred.connect(failed)
        logging.info('Playing audio on %s; startup protection=%d ms', self.output_name(), self.lead_ms)
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
        self._remember_activity()
        self.paused = True
        if self.player:
            self.player.pause()
        if self.speech:
            self.speech.pause(QTextToSpeech.BoundaryHint.Immediate)

    def resume(self):
        self.refresh_device()
        if not self.device_available and (self.player or self.decoder):
            self.failed.emit(self.active_token, 'Audio output unavailable. Connect speakers or headphones, then retry.')
            return
        self.paused = False
        if self.player:
            position = self.position()
            self._stop_player()
            self._play_pcm(self.active_token, position)
        if self.speech:
            self.speech.resume()

    def position(self):
        return self.source_offset + max(0, self.player.position() - self.lead_ms) if self.player else self.source_offset

    def _remember_activity(self):
        # Only real playback warms the device. Repeated stop/cancel calls and
        # pausing during initial silence must not bypass the next cold start.
        if self.player and self.device_available and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState and self.player.position() >= self.lead_ms:
            self.last_active = time.monotonic()

    def _stop_player(self):
        self._remember_activity()
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
