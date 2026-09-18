import logging
from PySide6.QtCore import Qt, QTimer, QByteArray
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QComboBox, QLabel, QMenu, QApplication, QMessageBox)
from PySide6.QtWidgets import QStyle, QStyleOptionComboBox, QStylePainter
from services.audio import Audio
from services.neural import NeuralService, VOICES
from services.sentences import split_sentences
from models.reader import Reader
from utils.storage import Settings
from ui.text_view import TextView

SPEEDS = [.6, .7, .8, .9, 1., 1.1, 1.2, 1.3, 1.5]


class VoiceCombo(QComboBox):
    """Full descriptive voice catalog, with a compact selected-voice label."""
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        key = self.currentData() or ''
        option.currentText = key.removeprefix('en-US-').replace('MultilingualNeural', '').replace('Neural', '')
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)


class ReaderWindow(QMainWindow):
    def __init__(self, neural=None, audio=None):
        super().__init__()
        self.store = Settings()
        data = self.store.load()
        self.reader = Reader(neural or NeuralService(), audio or Audio())
        self.dark = data.get('theme') == 'dark'
        self.font_size = max(14, min(40, int(data.get('font_size', 22))))
        self.mini = False
        self.normal_geometry = None
        self.setWindowTitle('English Reader')
        self.resize(620, 640)
        self.setMinimumSize(370, 270)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 12, 16, 12)
        self.header = QWidget()
        header = QHBoxLayout(self.header)
        header.setContentsMargins(0, 0, 0, 0)
        brand = QLabel('English Reader')
        brand.setObjectName('brand')
        header.addWidget(brand)
        header.addStretch()
        self.pin = QPushButton('Pin')
        self.pin.setCheckable(True)
        self.pin.toggled.connect(self.set_pin)
        header.addWidget(self.pin)
        self.settings_button = QPushButton('Settings')
        header.addWidget(self.settings_button)
        layout.addWidget(self.header)
        self.text = TextView()
        layout.addWidget(self.text, 1)
        self.failure_bar = QWidget()
        errors = QVBoxLayout(self.failure_bar)
        errors.setContentsMargins(0, 0, 0, 0)
        self.error_label = QLabel('Online neural voice unavailable.')
        self.error_label.setWordWrap(True)
        errors.addWidget(self.error_label)
        buttons = QHBoxLayout()
        self.retry_button = QPushButton('Retry')
        self.offline_button = QPushButton('Use Offline Voice')
        buttons.addWidget(self.retry_button)
        buttons.addWidget(self.offline_button)
        errors.addLayout(buttons)
        self.failure_bar.hide()
        layout.addWidget(self.failure_bar)
        controls = QHBoxLayout()
        self.previous = QPushButton('◀')
        self.play = QPushButton('▶')
        self.stop_button = QPushButton('■')
        self.next = QPushButton('▶▶')
        self.repeat = QPushButton('Repeat')
        for button, label in [(self.previous, 'Previous sentence (Ctrl+↑)'), (self.play, 'Play / pause (Space)'),
                              (self.stop_button, 'Stop (Esc)'), (self.next, 'Next sentence (Ctrl+↓)'), (self.repeat, 'Repeat current sentence (R)')]:
            button.setToolTip(label)
            button.setMinimumWidth(36)
            controls.addWidget(button)
        controls.addStretch()
        self.speed = QComboBox()
        for value in SPEEDS:
            self.speed.addItem(f'Speed {value:.1f}x', value)
        self.speed.setCurrentIndex(max(0, self.speed.findData(data.get('speed', .9))))
        controls.addWidget(self.speed)
        layout.addLayout(controls)
        self.voice_row = QWidget()
        voices = QHBoxLayout(self.voice_row)
        voices.setContentsMargins(0, 0, 0, 0)
        self.voice = VoiceCombo()
        self.voice.setMinimumWidth(100)
        self.voice.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        for key, label in VOICES.items():
            self.add_voice(key, label)
        saved_voice = data.get('voice', next(iter(VOICES)))
        if self.voice.findData(saved_voice) < 0 and isinstance(saved_voice, str) and saved_voice.startswith('en-US-'):
            self.add_voice(saved_voice, saved_voice)
        self.voice.setCurrentIndex(max(0, self.voice.findData(saved_voice)))
        voices.addWidget(self.voice, 1)
        self.preview = QPushButton('Preview')
        voices.addWidget(self.preview)
        self.mode = QComboBox()
        self.mode.addItems(['Continuous', 'Sentence Practice'])
        self.mode.setCurrentText(data.get('mode', 'Continuous'))
        voices.addWidget(self.mode)
        layout.addWidget(self.voice_row)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(450)
        self.save_timer.timeout.connect(self.save)
        self.text.textChanged.connect(self.text_changed)
        self.text.single.connect(lambda i: self.reader.read(i, True))
        self.text.double.connect(lambda i: self.reader.read(i, False))
        self.text.interrupt.connect(self.reader.stop)
        self.text.zoom.connect(self.change_font)
        self.reader.highlight.connect(self.mark)
        self.reader.changed.connect(self.refresh)
        self.reader.problem.connect(self.show_problem)
        self.reader.neural.voices.connect(self.available_voices)
        self.play.clicked.connect(self.reader.toggle)
        self.stop_button.clicked.connect(self.stop)
        self.previous.clicked.connect(lambda: self.reader.read(self.reader.index-1))
        self.next.clicked.connect(lambda: self.reader.read(self.reader.index+1))
        self.repeat.clicked.connect(lambda: self.reader.read(self.reader.index, False))
        self.preview.clicked.connect(self.reader.preview)
        self.retry_button.clicked.connect(lambda: self.retry(False))
        self.offline_button.clicked.connect(lambda: self.retry(True))
        self.speed.currentIndexChanged.connect(self.preferences)
        self.voice.currentIndexChanged.connect(self.preferences)
        self.mode.currentTextChanged.connect(self.mode_changed)
        self.menu = QMenu(self)
        self.action('Paste text', lambda: self.text.setPlainText(QApplication.clipboard().text()))
        self.edit_action = self.action('Edit text (Ctrl+E)', self.toggle_edit)
        self.action('Select all', self.text.selectAll)
        self.action('Clear text…', self.clear_text)
        self.menu.addSeparator()
        self.action('Formal American preset', self.formal)
        self.action('Larger text (Ctrl++)', lambda: self.change_font(1))
        self.action('Smaller text (Ctrl+-)', lambda: self.change_font(-1))
        self.action('Light / dark theme', self.toggle_theme)
        self.action('Mini Mode (Ctrl+M)', self.toggle_mini)
        self.action('Use online voice', lambda: self.retry(False))
        self.settings_button.setMenu(self.menu)
        self.text.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text.customContextMenuRequested.connect(lambda p: self.menu.exec(self.text.mapToGlobal(p)))
        for key, callback in {'Space': self.reader.toggle, 'R': lambda: self.reader.read(self.reader.index, False),
                              'Ctrl+Up': lambda: self.reader.read(self.reader.index-1), 'Ctrl+Down': lambda: self.reader.read(self.reader.index+1),
                              'Esc': self.stop, 'Ctrl+M': self.toggle_mini, 'Ctrl+L': self.pin.toggle,
                              'Ctrl+E': self.toggle_edit, 'Ctrl++': lambda: self.change_font(1),
                              'Ctrl+=': lambda: self.change_font(1), 'Ctrl+-': lambda: self.change_font(-1)}.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda cb=callback, k=key: cb() if self.text.isReadOnly() or k not in ('Space', 'R') else None)
            if key in ('Space', 'R'):
                # Editing must receive literal spaces and the letter R.
                setattr(self, 'space_shortcut' if key == 'Space' else 'repeat_shortcut', shortcut)
        self.text.setPlainText(data.get('text', ''))
        self.reader.index = max(0, min(int(data.get('index', 0)), len(self.reader.sentences)-1))
        self.preferences()
        self.pin.setChecked(bool(data.get('pin', False)))
        if data.get('geometry'):
            self.restoreGeometry(QByteArray.fromBase64(data['geometry'].encode()))
        if not any(s.availableGeometry().intersects(self.frameGeometry()) for s in QApplication.screens()):
            self.move(QApplication.primaryScreen().availableGeometry().topLeft())
        self.apply_theme()
        self.mark(self.reader.index, False)
        if data.get('mini'):
            self.toggle_mini()
            if data.get('mini_geometry'):
                self.restoreGeometry(QByteArray.fromBase64(data['mini_geometry'].encode()))
        self.refresh()

    def action(self, text, callback):
        action = QAction(text, self)
        action.triggered.connect(callback)
        self.menu.addAction(action)
        return action

    def add_voice(self, key, label):
        self.voice.addItem(label, key)
        self.voice.setItemData(self.voice.count()-1, label, Qt.ItemDataRole.ToolTipRole)

    def available_voices(self, voices):
        if not voices:
            return
        selected = self.reader.voice
        ordered = [v for v in VOICES if v in voices] + sorted(v for v in voices if v not in VOICES)
        self.voice.blockSignals(True)
        self.voice.clear()
        for voice in ordered:
            self.add_voice(voice, VOICES.get(voice, voice))
        self.voice.setCurrentIndex(max(0, self.voice.findData(selected)))
        self.voice.blockSignals(False)
        self.preferences()

    def preferences(self, *_):
        self.reader.voice = self.voice.currentData()
        self.reader.speed = self.speed.currentData()
        self.reader.mode = self.mode.currentText()
        self.voice.setToolTip(VOICES.get(self.reader.voice, self.reader.voice))
        self.save_timer.start()

    def mode_changed(self, *_):
        self.reader.continuous = self.mode.currentText() == 'Continuous'
        self.preferences()

    def text_changed(self):
        self.text.timer.stop()
        self.reader.set_sentences(split_sentences(self.text.toPlainText()))
        self.text.sentences = self.reader.sentences
        self.text.mark(-1)
        self.save_timer.start()
        self.refresh()

    def mark(self, index, follow=True):
        self.text.mark(index, self.dark, follow)
        self.save_timer.start()

    def refresh(self):
        reader = self.reader
        self.play.setText('Ⅱ' if reader.state in ('playing', 'loading') else '▶')
        self.preview.setText('End preview' if reader.preview_snapshot else 'Preview')
        source = 'Offline Windows Voice' if reader.offline else 'Online Neural Voice'
        self.setWindowTitle('English Reader' + (' · Offline Windows Voice' if reader.offline else ''))
        position = f'{reader.index+1} / {len(reader.sentences)}' if reader.sentences else 'Paste text to begin'
        self.status.setText(f'{source}  ·  {position}  ·  {reader.state.title()}')
        if reader.state != 'error':
            self.failure_bar.hide()
        self.save_timer.start()

    def show_problem(self, message):
        self.error_label.setText('Offline Windows voice unavailable.' if self.reader.offline else 'Online neural voice unavailable.')
        self.error_label.setToolTip(message)
        self.offline_button.setVisible(not self.reader.offline)
        self.failure_bar.show()

    def retry(self, offline):
        if not self.reader.sentences and not self.reader.preview_snapshot:
            self.reader.offline = offline
            self.refresh()
            return
        self.reader.retry(offline)

    def stop(self):
        self.text.timer.stop()
        self.reader.stop()

    def toggle_edit(self):
        self.stop()
        editing = self.text.isReadOnly()
        self.text.setReadOnly(not editing)
        self.space_shortcut.setEnabled(not editing)
        self.repeat_shortcut.setEnabled(not editing)
        self.edit_action.setText('Finish editing (Ctrl+E)' if editing else 'Edit text (Ctrl+E)')
        self.text.setFocus()
        if editing:
            self.status.setText('Editing text · Ctrl+E to return to reading')

    def clear_text(self):
        if QMessageBox.question(self, 'Clear text', 'Clear the saved reading text?') == QMessageBox.StandardButton.Yes:
            self.text.clear()

    def set_pin(self, enabled):
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if visible:
            self.show()
        if hasattr(self, 'save_timer'):
            self.save_timer.start()

    def change_font(self, delta):
        self.font_size = max(14, min(40, self.font_size + delta * 2))
        self.apply_theme()
        self.save_timer.start()

    def toggle_theme(self):
        self.dark = not self.dark
        self.apply_theme()
        self.mark(self.reader.index, False)

    def apply_theme(self):
        bg, panel, fg, border = ('#18222f', '#202e3d', '#e8eef5', '#3b4b5e') if self.dark else ('#f4f6f9', '#ffffff', '#26364a', '#d9e1eb')
        self.setStyleSheet(f'''
            QMainWindow, QWidget {{ background: {bg}; color: {fg}; font-family: 'Segoe UI'; font-size: 13px; }}
            QTextEdit {{ background: {panel}; border: 1px solid {border}; border-radius: 10px; padding: 20px; font-size: {self.font_size}px; selection-background-color: #779dc8; }}
            QPushButton, QComboBox {{ background: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 7px; }}
            QPushButton:hover {{ border-color: #4f85bc; }}
            QPushButton:checked {{ background: #355f89; color: white; }}
            QLabel#brand {{ font-size: 18px; font-weight: 600; }}
            QMenu {{ background: {panel}; border: 1px solid {border}; }}
            QMenu::item {{ padding: 7px 20px; }} QMenu::item:selected {{ background: #5279a0; color: white; }}
        ''')

    def formal(self):
        self.voice.setCurrentIndex(0)
        self.speed.setCurrentIndex(self.speed.findData(.9))
        self.preferences()

    def toggle_mini(self):
        self.mini = not self.mini
        for widget in (self.header, self.voice_row, self.previous, self.stop_button, self.repeat, self.status):
            widget.setVisible(not self.mini)
        if self.mini:
            self.normal_geometry = self.saveGeometry()
            self.setMinimumSize(300, 200)
            self.resize(360, 360)
        else:
            self.setMinimumSize(370, 270)
            if self.normal_geometry:
                self.restoreGeometry(self.normal_geometry)
        self.save_timer.start()

    def save(self):
        try:
            self.store.save(dict(text=self.text.toPlainText(), index=self.reader.index, font_size=self.font_size,
                                 voice=self.reader.voice, speed=self.reader.speed, mode=self.reader.mode,
                                 pin=self.pin.isChecked(), theme='dark' if self.dark else 'light', mini=self.mini,
                                 mini_geometry=bytes(self.saveGeometry().toBase64()).decode() if self.mini else None,
                                 geometry=bytes((self.normal_geometry if self.mini and self.normal_geometry else self.saveGeometry()).toBase64()).decode()))
        except OSError:
            logging.exception('Unable to save settings')
            self.status.setText('Auto Save failed. Check available disk space and folder permissions.')

    def closeEvent(self, event):
        self.save_timer.stop()
        self.save()
        self.stop()
        self.reader.neural.close()
        event.accept()
