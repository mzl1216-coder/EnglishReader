from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication
from services.sentences import split_sentences
from utils.storage import Settings


def complete(w):
    r = w.reader
    r.neural.ready.emit(r.token, 'test.mp3')
    r.audio.finished.emit(r.token)


def point(w, index):
    c = QTextCursor(w.text.document())
    c.setPosition(w.reader.sentences[index].start+2)
    w.text.setTextCursor(c)
    w.text.ensureCursorVisible()
    return w.text.cursorRect(c).center()


def test_parser():
    text = 'Dr. Smith works in the U.S. office. He paid 3.14 dollars! “Really?” Yes.'
    assert [s.text for s in split_sentences(text)] == ['Dr. Smith works in the U.S. office.', 'He paid 3.14 dollars!', '“Really?”', 'Yes.']
    assert split_sentences('😀 Hello. Next.')[1].start == 10
    assert not split_sentences('  \n ')


def test_single_click_continuous(window, qtbot):
    w = window
    qtbot.mouseClick(w.text.viewport(), Qt.MouseButton.LeftButton, pos=point(w, 4))
    assert not w.reader.neural.requests
    qtbot.wait(QApplication.doubleClickInterval()+80)
    assert w.reader.index == 4
    assert w.reader.continuous
    complete(w)
    assert w.reader.index == 5


def test_double_click_only_one(window, qtbot):
    w = window
    p = point(w, 9)
    qtbot.mouseClick(w.text.viewport(), Qt.MouseButton.LeftButton, pos=p)
    qtbot.mouseDClick(w.text.viewport(), Qt.MouseButton.LeftButton, pos=p)
    qtbot.wait(QApplication.doubleClickInterval()+80)
    assert len(w.reader.neural.requests) == 1
    assert w.reader.index == 9
    complete(w)
    assert w.reader.index == 9 and w.reader.state == 'completed'
    assert w.text.extraSelections()[0].cursor.selectedText() == w.reader.sentences[9].text
    qtbot.mouseDClick(w.text.viewport(), Qt.MouseButton.LeftButton, pos=point(w, 9))
    assert len(w.reader.neural.requests) == 2


def test_switch_discards_stale_audio(window):
    r = window.reader
    r.read(9)
    old = r.token
    r.read(2)
    r.neural.ready.emit(old, 'obsolete.mp3')
    r.audio.finished.emit(old)
    r.neural.failed.emit(old, 'obsolete error')
    assert not r.audio.plays
    assert r.index == 2 and r.state == 'loading'
    r.neural.ready.emit(r.token, 'new.mp3')
    assert r.state == 'playing'


def test_speed_applies_next_sentence(window):
    r = window.reader
    r.read(0)
    r.speed = 1.3
    assert r.neural.requests[-1][3] == .9
    complete(window)
    assert r.neural.requests[-1][3] == 1.3


def test_pause_while_loading_and_resume(window):
    r = window.reader
    r.read(0)
    r.toggle()
    r.neural.ready.emit(r.token, 'a.mp3')
    assert not r.audio.plays and r.state == 'paused'
    r.toggle()
    assert r.state == 'playing'
    r.toggle()
    assert r.state == 'paused'
    r.toggle()
    assert r.state == 'playing'


def test_practice_space_repeat(window, qtbot):
    r = window.reader
    r.mode = 'Sentence Practice'
    r.read(4)
    complete(window)
    qtbot.keyClick(window, Qt.Key.Key_Space)
    assert r.index == 5 and not r.continuous
    qtbot.keyClick(window, Qt.Key.Key_R)
    assert r.index == 5 and not r.continuous


def test_preview_restores_position(window):
    r = window.reader
    r.read(4)
    r.neural.ready.emit(r.token, 'article.mp3')
    r.preview()
    assert r.index == 4
    complete(window)
    assert r.index == 4 and r.state == 'loading'
    r.neural.ready.emit(r.token, 'article.mp3')
    assert r.audio.plays[-1][2] == 1234
    assert r.continuous


def test_network_failure_retry_offline(window):
    r = window.reader
    r.read(4)
    r.neural.failed.emit(r.token, 'network disconnected')
    assert r.state == 'error' and window.failure_bar.isVisible()
    window.retry(True)
    assert r.offline and r.state == 'playing'
    window.retry(False)
    r.neural.ready.emit(r.token, 'online.mp3')
    assert not r.offline and r.state == 'playing'


def test_auto_scroll_manual_override(window, qtbot):
    w = window
    w.reader.read(15)
    qtbot.wait(400)
    bar = w.text.verticalScrollBar()
    assert bar.value() > 0
    w.text.manual_scroll()
    bar.setValue(0)
    w.reader.read(16)
    qtbot.wait(400)
    assert bar.value() == 0
    w.text.manual_until = 0
    w.reader.read(17)
    qtbot.wait(400)
    assert bar.value() > 0


def test_save_restore_mini_pin_theme(window, qtbot):
    w = window
    w.reader.read(8, False)
    w.speed.setCurrentIndex(w.speed.findData(1.2))
    w.pin.setChecked(True)
    assert w.isVisible()
    w.toggle_theme()
    w.toggle_mini()
    assert not w.voice_row.isVisible()
    w.resize(320, 240)
    qtbot.wait(50)
    w.subtitle_hover(True)
    assert w.play.isVisible() and w.next.isVisible() and w.speed.isVisible()
    w.save()
    from ui.window import ReaderWindow
    from conftest import FakeAudio, FakeNeural
    other = ReaderWindow(FakeNeural(), FakeAudio())
    qtbot.addWidget(other)
    assert other.text.toPlainText() == w.text.toPlainText()
    assert other.reader.index == 8 and other.reader.speed == 1.2
    assert other.dark and other.mini and other.pin.isChecked()
    other.close()


def test_voice_fallback(window):
    window.available_voices(['en-US-AriaNeural', 'en-US-JennyNeural'])
    assert window.reader.voice == 'en-US-AriaNeural'


def test_edit_keeps_literal_shortcut_letters(window, qtbot):
    window.toggle_edit()
    window.text.clear()
    qtbot.keyClicks(window.text, 'Reader space')
    assert window.text.toPlainText() == 'Reader space'
    window.toggle_edit()
    assert window.text.isReadOnly()


def test_corrupt_settings(tmp_path, monkeypatch):
    monkeypatch.setenv('ENGLISHREADER_DATA_DIR', str(tmp_path))
    store = Settings()
    store.path.write_text('{broken')
    assert store.load() == {}
    store.path.write_text('{"font_size": "bad", "index": null, "speed": 500, "text": "keep this"}')
    assert store.load() == {'text': 'keep this'}


def test_preview_restores_paused_article(window):
    r = window.reader
    r.read(6)
    r.neural.ready.emit(r.token, 'article.mp3')
    r.toggle()
    r.preview()
    complete(window)
    assert r.state == 'paused' and r.index == 6
    r.neural.ready.emit(r.token, 'article.mp3')
    assert r.state == 'paused'
    r.toggle()
    assert r.state == 'playing' and r.audio.plays[-1][2] == 1234


def test_mode_change_finishes_current_then_stops(window):
    window.reader.read(0, True)
    window.mode.setCurrentText('Sentence Practice')
    complete(window)
    assert window.reader.index == 0 and window.reader.state == 'completed'


def test_resize_normal_and_mini_controls_fit(window, qtbot):
    for mini in (False, True):
        if mini:
            window.toggle_mini()
        window.resize(window.minimumSize())
        qtbot.wait(50)
        window.subtitle_hover(True)
        for widget in (window.play, window.next, window.speed):
            assert widget.isVisible()
            assert widget.geometry().right() <= window.centralWidget().width()
            assert widget.geometry().bottom() <= window.centralWidget().height()


def test_transparent_subtitles_hover_and_return(window, qtbot):
    window.toggle_mini()
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    window.subtitle_hover(False)
    assert not window.controls.isVisible()
    assert not window.mini_chrome.isVisible()
    assert not window.centralWidget().property('subtitleHover')
    image = window.grab().toImage()
    assert image.pixelColor(15, 15).alpha() < 5
    window.reader.read(2, False)
    assert window.text.extraSelections()[0].format.background().color().alpha() == 0
    window.subtitle_hover(True)
    assert window.controls.isVisible() and window.mini_chrome.isVisible()
    assert window.centralWidget().property('subtitleHover')
    window.toggle_mini()
    assert not window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.controls.isVisible() and window.header.isVisible()
    assert window.text.extraSelections()[0].format.background().color().alpha() == 255
