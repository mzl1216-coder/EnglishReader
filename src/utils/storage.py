import json
import os
from pathlib import Path


def directories():
    override = os.environ.get('ENGLISHREADER_DATA_DIR')
    roaming = Path(override or os.environ.get('APPDATA', Path.home())) / 'EnglishReader'
    local = Path(override or os.environ.get('LOCALAPPDATA', Path.home())) / 'EnglishReader'
    for path in (roaming, local / 'cache', local / 'logs'):
        path.mkdir(parents=True, exist_ok=True)
    return roaming, local


class Settings:
    def __init__(self):
        self.path = directories()[0] / 'settings.json'

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return {}
            types = dict(text=str, voice=str, speed=(int, float), index=int, font_size=int,
                         theme=str, mode=str, pin=bool, mini=bool, geometry=str, mini_geometry=str, output_device=str)
            clean = {k: v for k, v in data.items() if k in types and isinstance(v, types[k])}
            if clean.get('speed', .9) not in (.6, .7, .8, .9, 1., 1.1, 1.2, 1.3, 1.5):
                clean.pop('speed', None)
            if clean.get('mode', 'Continuous') not in ('Continuous', 'Sentence Practice'):
                clean.pop('mode', None)
            return clean
        except (OSError, ValueError):
            return {}

    def save(self, data):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)
