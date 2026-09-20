"""Small offline vocabulary plus an asynchronous, cached online dictionary."""
import html
import json
import logging
import re
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from utils.storage import directories


def normalize_word(word):
    word = word.strip().lower().replace('’', "'")
    return word if re.fullmatch(r"[a-z]+(?:['-][a-z]+)*", word) and len(word) <= 50 else ''


def parse_entry(payload):
    try:
        word = payload['ec']['word'][0]
        meanings = []
        for row in word.get('trs', []):
            for translation in row.get('tr', []):
                items = translation.get('l', {}).get('i', [])
                if isinstance(items, str):
                    items = [items]
                meanings.extend(s[:350] for s in items if isinstance(s, str))
        if not meanings:
            return None
        phone = word.get('usphone') or word.get('ukphone') or word.get('phone') or ''
        return {'phonetic': str(phone)[:100], 'meanings': meanings[:5], 'source': '有道词典'}
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def tooltip_html(word, entry):
    safe = html.escape
    if not entry:
        return f'<b>{safe(word)}</b><br>暂时无法查询，请检查网络或稍后重试。'
    phone = entry.get('phonetic') or '音标暂缺'
    meanings = '<br>'.join(safe(s) for s in entry.get('meanings', [])[:5])
    return f'<div style="max-width:340px"><b>{safe(word)}</b> &nbsp; /{safe(phone)}/<br>{meanings}<br><small>{safe(entry.get("source", "词典"))}</small></div>'


class DictionaryService(QObject):
    result = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.manager.setTransferTimeout(6000)
        self.reply = None
        self.cache = directories()[1] / 'cache' / 'dictionary'
        self.cache.mkdir(exist_ok=True)
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
        try:
            self.entries = json.loads((root / 'assets/dictionary.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.entries = {}

    def cancel(self):
        if self.reply:
            reply, self.reply = self.reply, None
            reply.abort()

    def lookup(self, raw_word):
        self.cancel()
        word = normalize_word(raw_word)
        if not word:
            return
        entry = self.entries.get(word)
        if not entry:
            try:
                stored = json.loads((self.cache / (word + '.json')).read_text(encoding='utf-8'))
                if isinstance(stored, dict) and isinstance(stored.get('meanings'), list) and stored['meanings'] and all(isinstance(s, str) for s in stored['meanings']) and isinstance(stored.get('phonetic', ''), str) and isinstance(stored.get('source', ''), str):
                    entry = stored
            except (OSError, ValueError):
                pass
        if entry:
            self.entries[word] = entry
            self.result.emit(word, entry)
            return
        url = QUrl('https://dict.youdao.com/jsonapi')
        query = QUrlQuery()
        query.addQueryItem('q', word)
        url.setQuery(query)
        request = QNetworkRequest(url)
        request.setRawHeader(b'User-Agent', b'EnglishReader/1.0.2')
        reply = self.manager.get(request)
        self.reply = reply

        def finished():
            if reply is not self.reply:
                reply.deleteLater()
                return
            self.reply = None
            entry = None
            if reply.error() == QNetworkReply.NetworkError.NoError:
                try:
                    raw = bytes(reply.readAll())
                    if len(raw) < 1_000_000:
                        entry = parse_entry(json.loads(raw))
                except (ValueError, TypeError):
                    pass
            if entry:
                self.entries[word] = entry
                try:
                    target = self.cache / (word + '.json')
                    temporary = target.with_suffix('.tmp')
                    temporary.write_text(json.dumps(entry, ensure_ascii=False), encoding='utf-8')
                    temporary.replace(target)
                except OSError:
                    logging.exception('Dictionary cache save failed')
            reply.deleteLater()
            self.result.emit(word, entry)
        reply.finished.connect(finished)
