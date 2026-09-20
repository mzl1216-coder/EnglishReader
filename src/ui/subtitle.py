"""Frameless subtitle chrome: hover controls, drag handle and resize edges."""
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QCursor
from shiboken6 import isValid


class SubtitleInteraction(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.targets = (window, window.centralWidget(), window.text, window.text.viewport(), window.mini_chrome, window.drag_label)
        for target in self.targets:
            target.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.Type.Enter, QEvent.Type.MouseButtonPress):
            return False
        w = self.window
        if not isValid(w) or not w.mini:
            return False
        if watched not in self.targets:
            return False
        if event.type() == QEvent.Type.Enter:
            w.subtitle_hover(True)
        elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            point = w.mapFromGlobal(event.globalPosition().toPoint())
            edges = Qt.Edge(0)
            if point.x() < 9:
                edges |= Qt.Edge.LeftEdge
            if point.x() > w.width()-10:
                edges |= Qt.Edge.RightEdge
            if point.y() < 9:
                edges |= Qt.Edge.TopEdge
            if point.y() > w.height()-10:
                edges |= Qt.Edge.BottomEdge
            if edges and w.windowHandle():
                w.windowHandle().startSystemResize(edges)
                return True
            if watched in (w.mini_chrome, w.drag_label) and w.windowHandle():
                w.windowHandle().startSystemMove()
                return True
        return False

    def check_hover(self):
        w = self.window
        if isValid(w) and w.mini and w.isVisible():
            # A shared geometry check avoids flicker when moving between child controls.
            w.subtitle_hover(w.frameGeometry().contains(QCursor.pos()) or w.menu.isVisible())
