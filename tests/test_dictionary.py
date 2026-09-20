from PySide6.QtCore import QPoint, QPointF, QEvent, Qt
from PySide6.QtGui import QTextCursor, QMouseEvent
from PySide6.QtWidgets import QToolTip, QApplication
from services.dictionary import normalize_word, parse_entry, tooltip_html


def test_dictionary_parser_and_untrusted_text():
    entry = parse_entry({'ec': {'word': [{'usphone': 'rɪsk', 'trs': [{'tr': [{'l': {'i': ['n. 风险', '<script>bad</script>']}}]}]}]}})
    assert entry['phonetic'] == 'rɪsk'
    assert entry['meanings'][0] == 'n. 风险'
    assert '<script>' not in tooltip_html('risk', entry)
    assert '&lt;script&gt;' in tooltip_html('risk', entry)
    assert parse_entry({'unexpected': []}) is None
    assert normalize_word('../escape') == ''
    assert normalize_word('Compliance') == 'compliance'
    assert normalize_word('123') == ''


def test_hover_word_displays_chinese_and_phonetic(window, qtbot):
    window.text.setPlainText('Compliance means following the rules.')
    cursor = QTextCursor(window.text.document())
    cursor.setPosition(3)
    point = window.text.cursorRect(cursor).center()
    assert window.text.word_at(point) == 'compliance'
    event = QMouseEvent(QEvent.Type.MouseMove, QPointF(point), QPointF(window.text.viewport().mapToGlobal(point)), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window.text.viewport(), event)
    qtbot.waitUntil(lambda: '合规' in QToolTip.text(), timeout=2000)
    assert 'kəmˈplaɪəns' in QToolTip.text()
    assert window.reader.neural.requests == []
    assert window.reader.state == 'idle'
    window.text.cancel_hover()
    assert window.lookup_word == ''


def test_offline_dictionary_cache_and_stale_hover(window, qtbot):
    with qtbot.waitSignal(window.dictionary.result) as signal:
        window.dictionary.lookup('opportunity')
    assert signal.args[1]['meanings'] == ['n. 机会；时机']
    window.lookup_word = 'risk'
    window.text.hover_word = 'risk'
    window.lookup_position = QPoint(100, 100)
    window.show_definition('opportunity', signal.args[1])
    assert '机会' not in QToolTip.text()


def test_returns_to_playing_sentence_after_fifteen_seconds(window, qtbot):
    r, text = window.reader, window.text
    r.read(15)
    r.neural.ready.emit(r.token, 'test.mp3')
    qtbot.wait(360)
    bar = text.verticalScrollBar()
    assert bar.value() > 0
    text.manual_scroll()
    bar.setValue(0)
    assert text.follow_timer.interval() == 15000
    qtbot.wait(200)
    r.read(16)
    r.neural.ready.emit(r.token, 'test.mp3')
    assert bar.value() == 0
    request_count = len(r.neural.requests)
    qtbot.waitUntil(lambda: bar.value() > 0, timeout=16000)
    assert r.index == 16
    assert len(r.neural.requests) == request_count


def test_scroll_countdown_restarts_and_pause_does_not_snap(window, qtbot):
    text = window.text
    window.reader.read(15)
    qtbot.wait(360)
    text.manual_scroll()
    qtbot.wait(80)
    before = text.follow_timer.remainingTime()
    text.manual_scroll()
    assert text.follow_timer.remainingTime() > before
    text.verticalScrollBar().setValue(0)
    window.reader.state = 'paused'
    text.finish_manual_scroll()
    qtbot.wait(360)
    assert text.verticalScrollBar().value() == 0
