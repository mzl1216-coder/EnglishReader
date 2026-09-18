import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import json
from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from utils.storage import directories


def main():
    roaming, local = directories()
    logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(local / 'logs' / 'app.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')], format='%(asctime)s %(levelname)s %(message)s')
    app = QApplication(sys.argv)
    app.setApplicationName('English Reader')
    app.setOrganizationName('EnglishReader')
    lock = QLockFile(str(roaming / 'app.lock'))
    if not lock.tryLock(100):
        QMessageBox.information(None, 'English Reader', 'English Reader is already running. Check your taskbar.')
        return 0
    def exception_hook(kind, value, traceback):
        logging.error('Unhandled application error', exc_info=(kind, value, traceback))
        QMessageBox.warning(None, 'English Reader', 'An unexpected error occurred. Your saved text is preserved. Details are in the app log.')
    sys.excepthook = exception_hook
    from ui.window import ReaderWindow
    window = ReaderWindow()
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    window.setWindowIcon(QIcon(str(root / 'assets' / 'icons' / 'app.ico')))
    window.show()
    if '--smoke-test' in sys.argv:
        def smoke():
            (local / 'smoke-test.json').write_text(json.dumps({'visible': window.isVisible(), 'frozen': bool(getattr(sys, 'frozen', False)), 'qt': True}), encoding='utf-8')
            window.close()
        QTimer.singleShot(2000, smoke)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
