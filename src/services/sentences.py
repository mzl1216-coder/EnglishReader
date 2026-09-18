"""Sentence spans preserve the original document and Qt UTF-16 offsets."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Sentence:
    text: str
    start: int
    end: int


def split_sentences(text):
    protected = set()
    for match in re.finditer(r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|e\.g|i\.e)\.|\b(?:[A-Za-z]\.){2,}|(?<=\d)\.(?=\d)", text, re.I):
        protected.update(range(match.start(), match.end()))
    boundaries = [m.end() for m in re.finditer(r'[.!?]+[\"\u201d\u2019\')\]]*(?=\s|$)|\n\s*\n', text) if m.start() not in protected]
    boundaries.append(len(text))
    result, start = [], 0
    for end in boundaries:
        raw = text[start:end]
        left = start + len(raw) - len(raw.lstrip())
        right = end - len(raw) + len(raw.rstrip())
        if right > left:
            result.append(Sentence(text[left:right], len(text[:left].encode('utf-16-le')) // 2,
                                   len(text[:right].encode('utf-16-le')) // 2))
        start = end
    return result
