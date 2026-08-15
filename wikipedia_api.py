#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import threading
import time
from typing import Dict, List, Optional, Set, Tuple

import requests

from config import (
    BATCH_SIZE,
    REQUEST_TIMEOUT,
    WIKI_API,
    WIKI_BASE_WAIT,
    WIKI_MAX_RETRIES,
    WIKI_MAX_WAIT,
    WIKI_MIN_INTERVAL,
    WIKI_USER_AGENT,
)
from logger_setup import get_logger, log_exception

logger = get_logger()

FA_WIKI_API = "https://fa.wikipedia.org/w/api.php"

_wiki_lock = threading.Lock()
_wiki_last_request = 0.0

def _wiki_wait() -> None:
    global _wiki_last_request
    with _wiki_lock:
        now = time.time()
        elapsed = now - _wiki_last_request
        if elapsed < WIKI_MIN_INTERVAL:
            time.sleep(WIKI_MIN_INTERVAL - elapsed)
        _wiki_last_request = time.time()

def wiki_get(params: dict, api_url: str = WIKI_API) -> dict:
    headers = {"User-Agent": WIKI_USER_AGENT}
    last_exc: Optional[Exception] = None

    for attempt in range(1, WIKI_MAX_RETRIES + 1):
        _wiki_wait()
        try:
            resp = requests.get(
                api_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 429:
                wait = min(WIKI_MAX_WAIT, WIKI_BASE_WAIT * (2 ** (attempt - 1)))
                logger.warning(
                    "Wikipedia 429 (attempt %d/%d). Waiting %ds...",
                    attempt, WIKI_MAX_RETRIES, wait,
                )
                time.sleep(wait)
                last_exc = RuntimeError(f"429 Too Many Requests (attempt {attempt})")
                continue

            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"Wikipedia API error: {data['error']}")
            return data

        except requests.exceptions.RequestException as e:
            wait = min(WIKI_MAX_WAIT, WIKI_BASE_WAIT * (2 ** (attempt - 1)))
            logger.warning(
                "Wikipedia network error (attempt %d/%d): %s | wait %ds",
                attempt, WIKI_MAX_RETRIES, e, wait,
            )
            time.sleep(wait)
            last_exc = e
        except Exception as e:
            if attempt == WIKI_MAX_RETRIES:
                raise RuntimeError(f"Error calling Wikipedia API: {e}") from e
            wait = min(40, 5 * attempt)
            logger.warning("Wikipedia unexpected error (attempt %d): %s | wait %ds", attempt, e, wait)
            time.sleep(wait)
            last_exc = e

    raise RuntimeError(f"Wikipedia API failed after {WIKI_MAX_RETRIES} retries. Last: {last_exc}")

def fetch_category_members(category: str, max_articles: int = 500) -> List[str]:
    cat = category.strip()
    if not cat.lower().startswith("category:"):
        cat = f"Category:{cat}"

    titles: List[str] = []
    cmcontinue = None

    while len(titles) < max_articles:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "categorymembers",
            "cmtitle": cat,
            "cmnamespace": "0",
            "cmtype": "page",
            "cmlimit": min(500, max_articles - len(titles)),
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        data = wiki_get(params)
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            title = m.get("title")
            if title:
                titles.append(title)

        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break

    return titles[:max_articles]

def filter_without_persian(titles: List[str], log_callback=None) -> List[str]:
    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    without_fa: List[str] = []
    total = len(titles)

    for i in range(0, total, BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "langlinks",
            "titles": "|".join(batch),
            "lllang": "fa",
            "lllimit": "max",
        }
        try:
            data = wiki_get(params)
        except Exception as e:
            log(f"خطا در بررسی langlinks برای دسته {i // BATCH_SIZE + 1}: {e}")
            log_exception(logger, "Details in filter_without_persian")
            without_fa.extend(batch)
            continue

        pages = data.get("query", {}).get("pages", [])
        has_fa: Set[str] = set()
        for page in pages:
            if page.get("missing"):
                continue
            title = page.get("title")
            langlinks = page.get("langlinks") or []
            if any(ll.get("lang") == "fa" for ll in langlinks):
                has_fa.add(title)

        for t in batch:
            if t not in has_fa:
                without_fa.append(t)

        log(
            f"بررسی langlinks: {min(i + BATCH_SIZE, total)}/{total} — بدون فارسی تا الان: {len(without_fa)}"
        )

    return without_fa

def fetch_wikitext(title: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": title,
        "redirects": "1",
    }
    data = wiki_get(params)
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        raise RuntimeError(f"صفحه‌ای با عنوان «{title}» پیدا نشد.")
    page = pages[0]
    if page.get("missing"):
        raise RuntimeError(f"مقاله «{title}» وجود ندارد.")
    revisions = page.get("revisions", [])
    if not revisions:
        raise RuntimeError(f"محتوای مقاله «{title}» در دسترس نیست.")
    content = revisions[0].get("slots", {}).get("main", {}).get("content")
    if not content:
        content = revisions[0].get("content")
    if not content:
        raise RuntimeError(f"ویکی‌کد مقاله «{title}» خالی است.")
    return content

_SKIP_LINK_PREFIXES = {
    "file", "image", "category", "template", "wikipedia", "w", "wp",
    "help", "portal", "module", "media", "special", "user", "talk",
    "project", "draft", "timedtext", "mediawiki",
    "رده", "پرونده", "تصویر", "الگو", "ویکی‌پدیا", "ویکی پدیا",
}

def get_internal_links(wikitext: str) -> List[str]:
    pattern = re.compile(r"\[\[+([^\]|#]+)(?:\|[^\]]*)?\]\]+", re.UNICODE)
    titles: List[str] = []
    seen: Set[str] = set()
    for m in pattern.finditer(wikitext):
        target = m.group(1).strip()
        if ":" in target:
            prefix = target.split(":", 1)[0].lower().strip()
            if prefix in _SKIP_LINK_PREFIXES:
                continue
        target = target.replace("_", " ").strip()
        if target and target not in seen:
            seen.add(target)
            titles.append(target)
    return titles

def extract_categories(wikitext: str) -> List[str]:
    pattern = re.compile(
        r"\[\[\s*(?:Category|رده)\s*:\s*([^\]|#]+?)(?:\|[^\]]*)?\s*\]\]",
        re.IGNORECASE | re.UNICODE,
    )
    cats: List[str] = []
    seen: Set[str] = set()
    for m in pattern.finditer(wikitext):
        name = m.group(1).strip().replace("_", " ")
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            cats.append(name)
    return cats

def get_fa_langlinks_map(titles: List[str]) -> tuple[Dict[str, str], Set[str]]:
    mapping: Dict[str, str] = {}
    no_fa: Set[str] = set()
    if not titles:
        return mapping, no_fa

    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "langlinks",
            "titles": "|".join(batch),
            "lllang": "fa",
            "lllimit": "max",
        }
        try:
            data = wiki_get(params)
        except Exception as e:
            logger.warning("Failed langlinks batch: %s", e)
            continue

        pages = data.get("query", {}).get("pages", [])
        found_in_batch = set()
        for page in pages:
            if page.get("missing"):
                continue
            en_title = page.get("title")
            if not en_title:
                continue
            found_in_batch.add(en_title)
            langlinks = page.get("langlinks") or []
            has_fa = False
            for ll in langlinks:
                if ll.get("lang") == "fa":
                    fa_title = ll.get("title") or ll.get("*")
                    if fa_title:
                        mapping[en_title] = fa_title
                        mapping[en_title.replace("_", " ")] = fa_title
                        has_fa = True
                    break
            if not has_fa:
                no_fa.add(en_title)
                no_fa.add(en_title.replace("_", " "))

        for t in batch:
            if t not in found_in_batch and t.replace("_", " ") not in found_in_batch:
                no_fa.add(t)
                no_fa.add(t.replace("_", " "))

    return mapping, no_fa

def get_fa_category_map(category_names: List[str]) -> Dict[str, str]:
    if not category_names:
        return {}
    prefixed = [f"Category:{c}" for c in category_names]
    mapping, _ = get_fa_langlinks_map(prefixed)
    result: Dict[str, str] = {}
    for en_full, fa_full in mapping.items():
        en_name = re.sub(r"^(?:Category|رده)\s*:\s*", "", en_full, flags=re.I).strip()
        fa_name = re.sub(r"^(?:Category|رده)\s*:\s*", "", fa_full, flags=re.I).strip()
        if en_name and fa_name:
            result[en_name] = fa_name
            result[en_name.replace("_", " ")] = fa_name
    return result

def strip_categories(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    cat_re = re.compile(
        r"^\s*(?:\[\[)?(?:Category|رده)\s*:\s*.*?(?:\]\])?\s*$",
        re.IGNORECASE | re.UNICODE,
    )
    for line in lines:
        if cat_re.match(line.strip()):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).rstrip() + "\n"

def adapt_categories(text: str, cat_map: Dict[str, str]) -> str:
    if not cat_map:
        return strip_categories(text)

    adapted: List[str] = []
    seen_fa: Set[str] = set()

    def cat_replacer(match: re.Match) -> str:
        name = match.group(1).strip().replace("_", " ")
        fa = cat_map.get(name) or cat_map.get(name.casefold())
        if not fa:
            for en, fa_val in cat_map.items():
                if en.casefold() == name.casefold():
                    fa = fa_val
                    break
        if fa and fa.casefold() not in seen_fa:
            seen_fa.add(fa.casefold())
            adapted.append(fa)
        return ""

    pattern = re.compile(
        r"\[\[\s*(?:Category|رده)\s*:\s*([^\]|#]+?)(?:\|[^\]]*)?\s*\]\]",
        re.IGNORECASE | re.UNICODE,
    )
    text = pattern.sub(cat_replacer, text)
    text = strip_categories(text)

    if adapted:
        lines = [f"[[رده:{c}]]" for c in adapted]
        text = text.rstrip() + "\n\n" + "\n".join(lines) + "\n"

    return text

def _normalize_title(s: str) -> str:
    if not s:
        return ""
    s = s.replace("_", " ").strip()
    s = s.replace("ي", "ی").replace("ك", "ک")
    s = s.replace("ى", "ی").replace("ة", "ه")
    s = s.replace("\u200c", "").replace("\u200f", "").replace("\u200e", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()

def extract_link_targets_from_text(text: str) -> List[str]:
    pattern = re.compile(r"\[\[+([^\]|#]+)(?:\|[^\]]*)?\]\]+", re.UNICODE)
    titles: List[str] = []
    seen: Set[str] = set()
    for m in pattern.finditer(text):
        target = m.group(1).strip()
        if ":" in target:
            prefix = target.split(":", 1)[0].lower().strip()
            if prefix in _SKIP_LINK_PREFIXES:
                continue
        key = _normalize_title(target)
        if key and key not in seen:
            seen.add(key)
            titles.append(target.replace("_", " ").strip())
    return titles

def check_pages_exist_on_fa(titles: List[str]) -> Dict[str, bool]:
    result: Dict[str, bool] = {}
    if not titles:
        return result

    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "info",
            "titles": "|".join(batch),
            "redirects": "1",
        }
        try:
            headers = {"User-Agent": WIKI_USER_AGENT}
            _wiki_wait()
            resp = requests.get(
                FA_WIKI_API, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 429:
                time.sleep(12)
                _wiki_wait()
                resp = requests.get(
                    FA_WIKI_API, params=params, headers=headers, timeout=REQUEST_TIMEOUT
                )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(
                "بررسی وجود صفحه روی ویکی فارسی شکست خورد (لینک‌ها حفظ می‌شوند): %s", e
            )
            continue

        pages = data.get("query", {}).get("pages", [])
        redirects = {}
        for r in data.get("query", {}).get("redirects", []) or []:
            if r.get("from") and r.get("to"):
                redirects[_normalize_title(r["from"])] = _normalize_title(r["to"])

        for page in pages:
            title = page.get("title") or ""
            exists = not page.get("missing", False)
            norm = _normalize_title(title)
            if norm:
                result[norm] = exists
            result[_normalize_title(title.replace(" ", "_"))] = exists

        for t in batch:
            nt = _normalize_title(t)
            if nt in result:
                continue
            if nt in redirects and redirects[nt] in result:
                result[nt] = result[redirects[nt]]

    return result

def remove_red_links(text: str) -> str:
    targets = extract_link_targets_from_text(text)
    if not targets:
        return text

    existence = check_pages_exist_on_fa(targets)
    if not existence:
        logger.warning(
            "نتیجه بررسی ویکی فارسی خالی بود — هیچ لینکی حذف نمی‌شود (fail-open)"
        )
        return text

    existing_count = sum(1 for v in existence.values() if v)
    missing_count = sum(1 for v in existence.values() if v is False)
    logger.info(
        "بررسی لینک‌ها روی ویکی فارسی: %d هدف → %d موجود / %d ناموجود / بقیه نامشخص",
        len(targets), existing_count, missing_count,
    )

    def replacer(match: re.Match) -> str:
        target = match.group(1).strip()
        display = match.group(2)

        if ":" in target:
            prefix = target.split(":", 1)[0].lower().strip()
            if prefix in _SKIP_LINK_PREFIXES:
                return match.group(0)

        norm = _normalize_title(target)
        exists = existence.get(norm)

        if exists is True:
            return match.group(0)
        if exists is False:
            if display and display.strip():
                return display.strip()
            return target
        return match.group(0)

    pattern = re.compile(
        r"\[\[+([^\]|#]+?)(?:\|([^\]]*?))?\]\]+",
        re.UNICODE,
    )
    return pattern.sub(replacer, text)

def apply_fa_titles_to_existing_links(text: str, fa_map: Dict[str, str]) -> str:
    if not fa_map:
        return text

    lookup: Dict[str, str] = {}
    for en, fa in fa_map.items():
        lookup[_normalize_title(en)] = fa

    def replacer(match: re.Match) -> str:
        target = match.group(1).strip()
        display = match.group(2)
        if ":" in target:
            return match.group(0)
        fa = lookup.get(_normalize_title(target))
        if not fa:
            return match.group(0)
        if display and display.strip():
            return f"[[{fa}|{display.strip()}]]"
        return f"[[{fa}]]"

    pattern = re.compile(
        r"\[\[+([^\]|#]+?)(?:\|([^\]]*?))?\]\]+",
        re.UNICODE,
    )
    return pattern.sub(replacer, text)

_PROTECT_TOKEN = "⟦WTP{0}⟧"
_PROTECT_RE = re.compile(r"⟦WTP(\d+)⟧")

def protect_wiki_structures(text: str) -> Tuple[str, List[str]]:
    store: List[str] = []

    def _mask(pattern: str, s: str, flags=re.DOTALL | re.IGNORECASE) -> str:
        def repl(m: re.Match) -> str:
            store.append(m.group(0))
            return _PROTECT_TOKEN.format(len(store) - 1)
        return re.sub(pattern, repl, s, flags=flags)

    protected = text
    protected = _mask(r"<ref\b[^>]*>.*?</ref>", protected)
    protected = _mask(r"<ref\b[^>]*/>", protected)
    protected = _mask(r"\[\[(?:File|Image|Media|پرونده|تصویر)\s*:.*?\]\]", protected)
    protected = _mask(r"<gallery\b[^>]*>.*?</gallery>", protected)
    protected = _mask(r"<nowiki>.*?</nowiki>", protected)
    protected = _mask(r"<pre\b[^>]*>.*?</pre>", protected)
    protected = _mask(r"<code\b[^>]*>.*?</code>", protected)
    protected = _mask(r"<math\b[^>]*>.*?</math>", protected)
    protected = _mask(r"<!--.*?-->", protected)

    for _ in range(40):
        prev = protected
        protected = _mask(r"\{\{[^{}]*\}\}", protected)
        if protected == prev:
            break

    return protected, store

def restore_wiki_structures(text: str, store: List[str]) -> str:
    if not store:
        return text

    def repl(m: re.Match) -> str:
        idx = int(m.group(1))
        if 0 <= idx < len(store):
            return store[idx]
        return m.group(0)

    for _ in range(len(store) + 2):
        if not _PROTECT_RE.search(text):
            break
        text = _PROTECT_RE.sub(repl, text)
    return text

def rebuild_plain_text_links(text: str, fa_map: Dict[str, str]) -> str:
    if not fa_map:
        return text

    items: List[Tuple[str, str]] = []
    seen = set()
    for en, fa in fa_map.items():
        en_clean = en.replace("_", " ").strip()
        key = _normalize_title(en_clean)
        if len(en_clean) < 3 or key in seen:
            continue
        seen.add(key)
        items.append((en_clean, fa))

    items.sort(key=lambda x: len(x[0]), reverse=True)

    protected, store = protect_wiki_structures(text)
    protected = _PROTECT_RE.sub(
        lambda m: _PROTECT_TOKEN.format(m.group(1)),
        protected,
    )

    for en, fa in items:
        pat = re.compile(r"(?<!\w)" + re.escape(en) + r"(?!\w)", re.IGNORECASE)
        protected = pat.sub(f"[[{fa}]]", protected)

    return restore_wiki_structures(protected, store)

def clean_translated_text(
    text: str,
    fa_map: Dict[str, str] | None = None,
    no_fa: Set[str] | None = None,
    cat_map: Dict[str, str] | None = None,
) -> str:
    if fa_map is None:
        fa_map = {}
    text = apply_fa_titles_to_existing_links(text, fa_map)
    text = rebuild_plain_text_links(text, fa_map)
    text = remove_red_links(text)
    if cat_map:
        text = adapt_categories(text, cat_map)
    else:
        text = strip_categories(text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"
