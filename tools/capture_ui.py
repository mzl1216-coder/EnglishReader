"""Render real Qt windows for visual QA without capturing the user's desktop."""
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
os.environ['ENGLISHREADER_DATA_DIR'] = str(ROOT / 'test-results/ui')
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from conftest import FakeAudio, FakeNeural
from ui.window import ReaderWindow
app = QApplication([])
w = ReaderWindow(FakeNeural(), FakeAudio())
if w.mini:
    w.toggle_mini()
w.show()
w.text.setPlainText('Thank you for giving me this opportunity.\n\nMy previous compliance experience was focused on business risk control.\n\nRecently, I have been working in international logistics, helping customers coordinate shipments across borders.\n\nNow I want to combine my compliance background with my experience in international business.\n\nI am committed to communicating clearly and finding practical solutions.')
w.reader.read(1, False)
QTest.qWait(500)
out = ROOT / 'test-results'
w.grab().save(str(out / 'normal.png'))
w.toggle_theme()
w.grab().save(str(out / 'dark.png'))
w.toggle_mini()
QTest.qWait(500)
w.subtitle_hover(False)
w.grab().save(str(out / 'mini.png'))
w.subtitle_hover(True)
w.grab().save(str(out / 'mini-hover.png'))
w.close()
