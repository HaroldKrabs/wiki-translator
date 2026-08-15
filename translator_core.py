#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from google.genai import types
from google.genai.errors import APIError, ClientError

from config import (
    INPUT_DIR,
    MAX_OUTPUT_TOKENS,
    MAX_RETRIES,
    MODEL_NAME,
    NETWORK_BASE_WAIT,
    NETWORK_MAX_WAIT,
    PROGRESS_DIR,
    RATE_LIMIT_BASE_WAIT,
    RATE_LIMIT_MAX_WAIT,
    REVIEW_MAX_CHARS,
    REVIEW_OVERLAP_CHARS,
    REVIEW_PROMPT,
    REVIEW_TEMPERATURE,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TITLE_TRANSLATE_PROMPT,
)
from key_manager import KeyManager
from logger_setup import get_logger, log_exception
from utils import (
    _is_network_error,
    content_hash,
    count_structural_elements,
    safe_filename,
    split_into_chunks,
    validate_chunk,
)
from wikipedia_api import (
    clean_translated_text,
    extract_categories,
    fetch_wikitext,
    get_fa_category_map,
    get_fa_langlinks_map,
    get_internal_links,
    protect_wiki_structures,
    restore_wiki_structures,
)

logger = get_logger()

def call_gemini(
    key_manager: KeyManager,
    preferred_key: Optional[str],
    user_content: str,
    system_instruction: str = SYSTEM_PROMPT,
    temperature: float = TEMPERATURE,
) -> Tuple[str, str]:
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client, key = key_manager.wait_and_get(preferred_key)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                ),
            )
            content = (response.text or "").strip()
            if not content:
                raise APIError("Empty response from model")
            key_manager.report_success(key)
            return content, key

        except RuntimeError:
            raise

        except ClientError as e:
            msg = str(e)
            is_rate = (
                "429" in msg
                or "RESOURCE_EXHAUSTED" in msg.upper()
                or "rate" in msg.lower()
                or "quota" in msg.lower()
            )
            if is_rate:
                if preferred_key:
                    key_manager.report_rate_limit(preferred_key)
                wait = min(RATE_LIMIT_MAX_WAIT, RATE_LIMIT_BASE_WAIT * attempt)
                logger.warning(
                    "429 / rate limit (attempt %d/%d). Waiting %ds...",
                    attempt, MAX_RETRIES, wait,
                )
                time.sleep(wait)
            elif "401" in msg or "UNAUTHENTICATED" in msg.upper() or "API_KEY" in msg.upper():
                if preferred_key:
                    key_manager.report_invalid(preferred_key)
                logger.error("Invalid API key: %s", msg)
                last_exc = e
            else:
                last_exc = e
                wait = min(30, 4 * attempt)
                time.sleep(wait)

        except Exception as e:
            last_exc = e
            if _is_network_error(e):
                wait = min(NETWORK_MAX_WAIT, NETWORK_BASE_WAIT * attempt)
                logger.warning("Network error (attempt %d/%d): %s | wait %ds", attempt, MAX_RETRIES, e, wait)
                time.sleep(wait)
            else:
                logger.warning("Gemini error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
                time.sleep(min(20, 3 * attempt))

    raise RuntimeError(f"Gemini failed after {MAX_RETRIES} retries. Last: {last_exc}")

def translate_title(
    key_manager: KeyManager,
    preferred_key: str,
    english_title: str,
) -> str:
    try:
        result, _ = call_gemini(
            key_manager,
            preferred_key,
            english_title,
            system_instruction=TITLE_TRANSLATE_PROMPT,
            temperature=0.1,
        )
        line = result.strip().splitlines()[0].strip().strip('"«»')
        return line or english_title
    except Exception as e:
        logger.warning(
            "Title translation failed for «%s»: %s — using English title",
            english_title, e,
        )
        return english_title

def _links_in_chunk(chunk: str) -> List[str]:
    return get_internal_links(chunk)

def _build_translate_prompt(chunk: str, links: List[str]) -> str:
    if not links:
        return chunk
    sample = links[:40]
    link_list = "\n".join(f"- [[{t}]]" for t in sample)
    extra = (
        "\n\n────────\n"
        "دستور اجباری برای این تکه:\n"
        "پیوندهای داخلی زیر را حتماً به صورت [[Target]] در خروجی نگه دار "
        "(Target را ترجمه نکن):\n"
        f"{link_list}\n"
        "────────\n"
    )
    return chunk + extra

def _split_for_review(text: str) -> List[str]:
    if len(text) <= REVIEW_MAX_CHARS:
        return [text]

    parts: List[str] = []
    paragraphs = re.split(r"(\n\n+)", text)
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) <= REVIEW_MAX_CHARS:
            buf += p
        else:
            if buf.strip():
                parts.append(buf)
            if len(p) > REVIEW_MAX_CHARS:
                for i in range(0, len(p), REVIEW_MAX_CHARS):
                    parts.append(p[i : i + REVIEW_MAX_CHARS])
                buf = ""
            else:
                buf = p
    if buf.strip():
        parts.append(buf)
    return parts or [text]

def review_article(
    key_manager: KeyManager,
    preferred_key: str,
    text: str,
    log=None,
) -> str:
    def _log(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    chunks = _split_for_review(text)
    if len(chunks) == 1:
        _log("بازبینی نهایی: ۱ تکه")
    else:
        _log(f"بازبینی نهایی: {len(chunks)} تکه (مقاله بلند)")

    reviewed: List[str] = []
    prev_tail = ""

    for i, chunk in enumerate(chunks):
        _log(f"  بازبینی تکه {i + 1}/{len(chunks)} ({len(chunk)} کاراکتر)")
        user_parts = []
        if prev_tail:
            user_parts.append(
                "متن قبلی (فقط برای انسجام لحن و واژگان؛ در خروجی تکرار نکن):\n"
                f"{prev_tail}\n"
            )
        user_parts.append("متن نیازمند بازبینی:\n" + chunk)
        user_content = "\n".join(user_parts)

        best = None
        for attempt in range(3):
            try:
                result, _ = call_gemini(
                    key_manager,
                    preferred_key,
                    user_content,
                    system_instruction=REVIEW_PROMPT,
                    temperature=REVIEW_TEMPERATURE,
                )
                if len(result.strip()) < max(50, int(len(chunk) * 0.45)):
                    _log(f"  بازبینی تکه {i + 1}: خروجی خیلی کوتاه بود (تلاش {attempt + 1})")
                    best = result if best is None else best
                    continue
                o_links = count_structural_elements(chunk)["links"]
                t_links = count_structural_elements(result)["links"]
                if o_links >= 2 and t_links < max(1, o_links // 2):
                    _log(f"  بازبینی تکه {i + 1}: افت لینک (تلاش {attempt + 1})")
                    best = result if best is None else best
                    continue
                best = result
                break
            except Exception as e:
                _log(f"  خطا در بازبینی تکه {i + 1}: {e}")
                log_exception(logger, f"Review chunk {i + 1}")
                if attempt == 2:
                    best = chunk
                    break

        if best is None:
            best = chunk
        reviewed.append(best)
        prev_tail = best[-REVIEW_OVERLAP_CHARS:] if len(best) > REVIEW_OVERLAP_CHARS else best

    return "\n\n".join(reviewed)

def process_article(
    key_manager: KeyManager,
    preferred_key: str,
    title: str,
    category_folder: Path,
    log_callback=None,
) -> Tuple[Optional[str], List[str]]:
    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    log(f"شروع ترجمه: {title} (کلید ترجیحی ...{preferred_key[-8:]})")

    try:
        original_text = fetch_wikitext(title)
        log(f"ویکی‌کد «{title}» دریافت شد ({len(original_text)} کاراکتر)")
    except Exception as e:
        log(f"خطا در دریافت «{title}»: {e}")
        log_exception(logger, f"Details fetching {title}")
        raise

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_en = safe_filename(title)
    input_path = INPUT_DIR / f"{safe_en}.txt"
    try:
        input_path.write_text(original_text, encoding="utf-8")
    except Exception as e:
        logger.warning("Could not save input file: %s", e)

    try:
        en_links = get_internal_links(original_text)
        log(f"تعداد لینک داخلی استخراج‌شده: {len(en_links)}")
        fa_map, no_fa = get_fa_langlinks_map(en_links)
        log(f"از این تعداد، {len(fa_map)} لینک نسخه فارسی دارند (و {len(no_fa)} بدون فارسی)")
    except Exception as e:
        logger.warning("خطا در استخراج/بررسی لینک‌ها: %s", e)
        fa_map, no_fa = {}, set()

    cat_map: dict = {}
    try:
        en_cats = extract_categories(original_text)
        if en_cats:
            log(f"تعداد دسته استخراج‌شده: {len(en_cats)}")
            cat_map = get_fa_category_map(en_cats)
            log(f"از این تعداد، {len(cat_map)} دسته نسخه فارسی دارند")
        else:
            log("دسته‌ای در متن مبدأ یافت نشد")
    except Exception as e:
        logger.warning("خطا در استخراج/تطبیق دسته‌ها: %s", e)
        cat_map = {}

    persian_title = translate_title(key_manager, preferred_key, title)
    log(f"عنوان فارسی: «{persian_title}»")

    file_hash = content_hash(original_text)
    progress_file = PROGRESS_DIR / f"{safe_en}_{file_hash}.json"
    progress = {}
    if progress_file.exists():
        try:
            progress = json.loads(progress_file.read_text(encoding="utf-8"))
            log(f"پیشرفت قبلی «{title}» بارگذاری شد.")
        except Exception as e:
            logger.warning("Error reading progress file: %s", e)
            progress = {}

    chunks = split_into_chunks(original_text)
    log(f"«{title}» → {len(chunks)} تکه ترجمه (بخش‌محور)")

    translated_chunks = progress.get("translated", [None] * len(chunks))
    if len(translated_chunks) != len(chunks):
        translated_chunks = [None] * len(chunks)

    flagged: List[str] = []

    for i, chunk in enumerate(chunks):
        if translated_chunks[i] is not None:
            continue

        links = _links_in_chunk(chunk)
        protected_chunk, protect_store = protect_wiki_structures(chunk)
        user_content = _build_translate_prompt(protected_chunk, links)
        log(f"  [{title}] تکه {i + 1}/{len(chunks)} ({len(chunk)} کاراکتر، {len(links)} لینک، {len(protect_store)} بخش محافظت‌شده)")

        success = False
        result = None
        best_result = None

        for retry in range(4):
            try:
                raw_result, _ = call_gemini(key_manager, preferred_key, user_content)
                result = restore_wiki_structures(raw_result, protect_store) if raw_result else raw_result
                if result and len(result.strip()) > len(best_result or ""):
                    best_result = result
                if validate_chunk(chunk, result):
                    translated_chunks[i] = result
                    success = True
                    break
                log(
                    f"  اعتبارسنجی تکه {i + 1} رد شد ({retry + 1}/4) — "
                    f"طول={len(result) if result else 0}"
                )
            except RuntimeError as e:
                log(str(e))
                progress = {
                    "file_hash": file_hash,
                    "total_chunks": len(chunks),
                    "translated": translated_chunks,
                    "persian_title": persian_title,
                }
                try:
                    progress_file.write_text(
                        json.dumps(progress, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                raise
            except Exception as e:
                log(f"  خطا در تکه {i + 1}: {e}")
                log_exception(logger, f"Chunk {i + 1} of {title}")
                if retry == 3:
                    break

        if not success:
            if best_result is not None:
                translated_chunks[i] = best_result
                log(f"  تکه {i + 1}: بهترین خروجی موجود نگه داشته شد")
            elif result is not None:
                translated_chunks[i] = result
            else:
                translated_chunks[i] = f"<!-- ترجمه تکه {i + 1} ناموفق بود -->\n{chunk[:500]}"
                log(f"  هشدار: تکه {i + 1} بدون خروجی")
            flagged.append(f"{title} → تکه {i + 1}")

        progress = {
            "file_hash": file_hash,
            "total_chunks": len(chunks),
            "translated": translated_chunks,
            "persian_title": persian_title,
        }
        try:
            progress_file.write_text(
                json.dumps(progress, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Could not save progress: %s", e)

    for i, c in enumerate(translated_chunks):
        if c is None:
            log(f"هشدار جدی: تکه {i + 1} خالی — جایگزین با اصل")
            translated_chunks[i] = chunks[i]
            flagged.append(f"{title} → تکه {i + 1} (اصل)")

    final_text = "\n\n".join(translated_chunks)
    try:
        o_links = count_structural_elements(original_text)["links"]
        t_links = count_structural_elements(final_text)["links"]
        log(f"پیوندها پس از ترجمه: اصل={o_links} | ترجمه={t_links}")
    except Exception:
        pass

    try:
        final_text = clean_translated_text(final_text, fa_map, no_fa, cat_map=cat_map)
        log("پاک‌سازی + بازسازی لینک‌ها + تطبیق دسته‌ها انجام شد")
        try:
            after = count_structural_elements(final_text)["links"]
            log(f"پیوندها پس از بازسازی/پاک‌سازی: {after}")
        except Exception:
            pass
    except Exception as e:
        logger.warning("خطا در پاک‌سازی/بازسازی لینک: %s", e)

    try:
        final_text = review_article(key_manager, preferred_key, final_text, log=log)
        log("بازبینی نهایی AI تمام شد")
        final_text = clean_translated_text(final_text, fa_map, no_fa, cat_map=cat_map)
    except Exception as e:
        log(f"خطا در بازبینی نهایی (متن ترجمه‌شده ذخیره می‌شود): {e}")
        log_exception(logger, f"Review stage for {title}")

    category_folder.mkdir(parents=True, exist_ok=True)
    safe_fa = safe_filename(persian_title)
    output_path = category_folder / f"{safe_fa}.txt"
    try:
        output_path.write_text(final_text, encoding="utf-8")
        log(f"ذخیره شد: {output_path.relative_to(category_folder.parent.parent)}")
    except Exception as e:
        log(f"خطا در ذخیره فایل خروجی: {e}")
        raise

    try:
        progress_file.unlink(missing_ok=True)
    except Exception:
        pass

    return persian_title, flagged
