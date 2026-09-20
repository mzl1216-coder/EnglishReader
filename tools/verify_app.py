"""Exercise the real window, neural worker and audio together (network opt-in)."""
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
OUT = ROOT / 'test-results/integration'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['ENGLISHREADER_DATA_DIR'] = str(OUT)
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from ui.window import ReaderWindow
app = QApplication([])
w = ReaderWindow()
w.show()
w.text.setPlainText('\n\n'.join(f'This is sentence {i}.' for i in range(1, 21)))
events = []
phase = [0]
result = {'passed': False}


def tick():
    r = w.reader
    state = (r.index, r.state, bool(r.preview_snapshot))
    if not events or events[-1] != state:
        events.append(state)
    if r.state == 'error':
        result['error'] = w.error_label.toolTip()
        finish()
    elif phase[0] == 0 and r.index == 5:
        phase[0] = 1
        r.read(9, False)
    elif phase[0] == 1 and r.index == 9 and r.state == 'playing':
        phase[0] = 2
        r.read(2, False)
    elif phase[0] == 2 and r.index == 2 and r.state == 'completed':
        phase[0] = 3
        r.preview()
    elif phase[0] == 3 and not r.preview_snapshot and r.state == 'completed':
        assert r.index == 2
        phase[0] = 4
        r.offline = True
        r.read(3, False)
    elif phase[0] == 4 and r.index == 3 and r.state == 'completed':
        result['passed'] = True
        finish()


def finish():
    timer.stop()
    deadline.stop()
    result['events'] = events
    (OUT / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    w.grab().save(str(OUT / 'window.png'))
    w.close()


timer = QTimer()
timer.timeout.connect(tick)
timer.start(50)
deadline = QTimer()
deadline.setSingleShot(True)
deadline.timeout.connect(finish)
deadline.start(90000)
w.reader.read(4, True)
app.exec()
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
