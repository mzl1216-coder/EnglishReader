import time
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import QTextEdit, QApplication


class TextView(QTextEdit):
    single = Signal(int)
    double = Signal(int)
    interrupt = Signal()
    zoom = Signal(int)

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setAcceptRichText(False)
        self.setPlaceholderText('Paste English text with Ctrl+V to begin.\n\nClick a sentence to read continuously.\nDouble-click to hear just that sentence.')
        self.sentences = []
        self.pending_index = -1
        self.manual_until = 0
        self.press_position = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.single.emit(self.pending_index))
        self.scroll = QPropertyAnimation(self.verticalScrollBar(), b'value', self)
        self.scroll.setDuration(320)
        self.scroll.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.verticalScrollBar().sliderPressed.connect(self.manual_scroll)

    def manual_scroll(self):
        self.manual_until = time.monotonic() + 1.8
        self.scroll.stop()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom.emit(1 if event.angleDelta().y() > 0 else -1)
            event.accept()
        else:
            self.manual_scroll()
            super().wheelEvent(event)

    def sentence_at(self, point):
        position = self.cursorForPosition(point).position()
        return next((i for i, s in enumerate(self.sentences) if s.start <= position < s.end), -1)

    def mousePressEvent(self, event):
        self.timer.stop()
        self.press_position = event.position().toPoint()
        if self.isReadOnly() and event.button() == Qt.MouseButton.LeftButton:
            self.pending_index = self.sentence_at(self.press_position)
            if self.pending_index >= 0:
                self.interrupt.emit()
                self.timer.start(QApplication.doubleClickInterval() + 30)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.press_position is not None and (event.position().toPoint() - self.press_position).manhattanLength() > QApplication.startDragDistance():
            self.timer.stop()
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.isReadOnly() and event.button() == Qt.MouseButton.LeftButton:
            self.timer.stop()
            index = self.sentence_at(event.position().toPoint())
            if index >= 0:
                self.double.emit(index)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if self.isReadOnly() and event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            self.setPlainText(QApplication.clipboard().text())
            event.accept()
        else:
            if event.key() in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown, Qt.Key.Key_Home, Qt.Key.Key_End):
                self.manual_scroll()
            super().keyPressEvent(event)

    def mark(self, index, dark=False, follow=True, subtitle=False):
        if not 0 <= index < len(self.sentences):
            self.setExtraSelections([])
            return
        sentence = self.sentences[index]
        cursor = QTextCursor(self.document())
        cursor.setPosition(sentence.start)
        cursor.setPosition(sentence.end, QTextCursor.MoveMode.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.format = QTextCharFormat()
        selection.format.setBackground(QColor(0, 0, 0, 0) if subtitle else QColor('#334b66' if dark else '#fff0b3'))
        selection.format.setForeground(QColor('#000000') if subtitle else QColor('#f5f7fa' if dark else '#192d43'))
        if subtitle:
            selection.format.setFontWeight(600)
        self.setExtraSelections([selection])
        if follow and time.monotonic() >= self.manual_until and not self.verticalScrollBar().isSliderDown():
            cursor.setPosition(sentence.start)
            bar = self.verticalScrollBar()
            target = bar.value() + self.cursorRect(cursor).top() - int(self.viewport().height() * .43)
            self.scroll.stop()
            self.scroll.setStartValue(bar.value())
            self.scroll.setEndValue(max(bar.minimum(), min(bar.maximum(), target)))
            self.scroll.start()
