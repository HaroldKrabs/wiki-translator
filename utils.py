#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import re
from typing import List

from config import (
    MAX_CHARS_PER_CHUNK,
    MAX_PARAGRAPHS_PER_CHUNK,
    PERSIAN_ALPHABET,
)

HEADING_PATTERN = re.compile(r"^\s*(={2,6})\s*.*?\s*\1\s*$")
SECTION_SPLIT = re.compile(r"(?=^\s*={2,6}\s)", re.MULTILINE)

def safe_filename(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", title)
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    return name[:120] or "untitled"

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def _split_paragraphs_into_chunks(paragraphs: List[str]) -> List[str]:
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        plen = len(p)

        if plen > MAX_CHARS_PER_CHUNK:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            for i in range(0, plen, MAX_CHARS_PER_CHUNK):
                chunks.append(p[i : i + MAX_CHARS_PER_CHUNK])
            continue

        would_exceed = (
            current
            and (
                current_len + plen + 2 > MAX_CHARS_PER_CHUNK
                or len(current) >= MAX_PARAGRAPHS_PER_CHUNK
            )
        )
        if would_exceed:
            chunks.append("\n\n".join(current))
            current = [p]
            current_len = plen
        else:
            current.append(p)
            current_len += plen + (2 if current_len else 0)

    if current:
        chunks.append("\n\n".join(current))
    return chunks

def split_into_chunks(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []

    parts = SECTION_SPLIT.split(text)
    sections: List[str] = []
    for part in parts:
        part = part.strip()
        if part:
            sections.append(part)

    if not sections:
        sections = [text]

    chunks: List[str] = []
    for section in sections:
        if len(section) <= MAX_CHARS_PER_CHUNK:
            paras = re.split(r"\n\s*\n", section)
            if len(paras) <= MAX_PARAGRAPHS_PER_CHUNK and len(section) <= MAX_CHARS_PER_CHUNK:
                chunks.append(section)
            else:
                chunks.extend(_split_paragraphs_into_chunks(paras))
        else:
            paras = re.split(r"\n\s*\n", section)
            chunks.extend(_split_paragraphs_into_chunks(paras))

    final: List[str] = []
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        if len(c) > MAX_CHARS_PER_CHUNK * 1.5:
            for i in range(0, len(c), MAX_CHARS_PER_CHUNK):
                piece = c[i : i + MAX_CHARS_PER_CHUNK].strip()
                if piece:
                    final.append(piece)
        else:
            final.append(c)
    return final or [text]

def count_structural_elements(text: str) -> dict:
    return {
        "ref": len(re.findall(r"<ref[\s>/]", text, re.IGNORECASE)),
        "headings": len(HEADING_PATTERN.findall(text)),
        "links": len(re.findall(r"\[\[+", text)),
        "templates": len(re.findall(r"\{\{", text)),
    }

def validate_chunk(original: str, translated: str) -> bool:
    if not translated or not translated.strip():
        return False
    if len(translated.strip()) < max(40, int(len(original) * 0.15)):
        return False
    o = count_structural_elements(original)
    t = count_structural_elements(translated)
    if abs(o["ref"] - t["ref"]) > 2:
        return False
    if abs(o["headings"] - t["headings"]) > 1:
        return False
    if o["links"] >= 3 and t["links"] < max(1, o["links"] // 2):
        return False
    o_cjk = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]", original))
    t_cjk = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]", translated))
    if o_cjk >= 5 and t_cjk < max(1, o_cjk // 3):
        return False
    return True

def _is_network_error(exc: Exception) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    network_names = (
        "RemoteProtocolError",
        "ConnectError",
        "ReadTimeout",
        "WriteTimeout",
        "ConnectTimeout",
        "PoolTimeout",
        "NetworkError",
        "ProxyError",
        "ProtocolError",
    )
    if name in network_names:
        return True
    keywords = (
        "server disconnected",
        "connection reset",
        "connection aborted",
        "connection refused",
        "timed out",
        "timeout",
        "temporarily unavailable",
        "broken pipe",
        "network is unreachable",
    )
    return any(k in msg for k in keywords)

_NORM_MAP = str.maketrans({
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ه",
    "ۀ": "ه",
    "أ": "ا",
    "إ": "ا",
    "آ": "آ",
})

_WEIGHTS = {char: idx for idx, char in enumerate(PERSIAN_ALPHABET)}

def persian_sort_key(s: str) -> list:
    if not isinstance(s, str):
        return [0]

    s = s.translate(_NORM_MAP).casefold()
    key: list = []

    for char in s:
        if char == " ":
            key.append(-100)
        elif char == "\u200c":
            key.append(-99)
        elif char.isdigit() or char in "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩":
            digit_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
            try:
                digit_val = int(char.translate(digit_map))
                key.append(-50 + digit_val)
            except ValueError:
                key.append(ord(char))
        elif char in _WEIGHTS:
            key.append(1000 + _WEIGHTS[char])
        else:
            key.append(ord(char))

    return key

def persian_sorted(items: list[str]) -> list[str]:
    return sorted(items, key=persian_sort_key)
