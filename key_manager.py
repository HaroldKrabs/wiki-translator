#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from google import genai
from google.genai.errors import ClientError

from config import (
    KEY_COOLDOWN_ON_429,
    MAX_DAILY_REQUESTS,
    MIN_REQUEST_INTERVAL,
    RATE_LIMIT_BASE_WAIT,
    RATE_LIMIT_MAX_WAIT,
)
from logger_setup import get_logger

logger = get_logger()

@dataclass
class KeyState:
    key: str
    client: Optional[genai.Client] = None
    last_request: float = 0.0
    daily_count: int = 0
    daily_reset: float = field(default_factory=lambda: time.time() + 86400)
    cooldown_until: float = 0.0
    consecutive_429: int = 0
    total_errors: int = 0
    is_valid: bool = True

    @property
    def short(self) -> str:
        return f"...{self.key[-8:]}" if len(self.key) > 8 else self.key

class KeyManager:

    def __init__(self, api_keys: List[str]):
        if not api_keys:
            raise ValueError("At least one API key is required")

        self._lock = threading.RLock()
        self.keys: Dict[str, KeyState] = {}

        for k in api_keys:
            state = KeyState(key=k)
            try:
                state.client = genai.Client(api_key=k)
                logger.info("Client created for key %s", state.short)
            except Exception as e:
                logger.error("Failed to create client for %s: %s", state.short, e)
                state.is_valid = False
            self.keys[k] = state

        self._valid_keys = [k for k, s in self.keys.items() if s.is_valid]
        if not self._valid_keys:
            raise RuntimeError("No valid API keys available")

        logger.info("KeyManager ready with %d valid key(s)", len(self._valid_keys))

    def _reset_daily_if_needed(self, state: KeyState) -> None:
        now = time.time()
        if now > state.daily_reset:
            state.daily_count = 0
            state.daily_reset = now + 86400
            state.consecutive_429 = 0
            logger.debug("Daily counter reset for %s", state.short)

    def _select_best_key(self) -> Optional[KeyState]:
        now = time.time()
        candidates = []

        for k in self._valid_keys:
            state = self.keys[k]
            self._reset_daily_if_needed(state)

            if not state.is_valid:
                continue
            if now < state.cooldown_until:
                continue
            if state.daily_count >= MAX_DAILY_REQUESTS:
                continue

            score = (
                state.consecutive_429,
                state.daily_count,
                state.last_request,
                state.total_errors,
            )
            candidates.append((score, state))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def wait_and_get(self, preferred_key: Optional[str] = None) -> tuple[genai.Client, str]:
        max_wait = 300
        start = time.time()

        while True:
            with self._lock:
                state: Optional[KeyState] = None

                if preferred_key and preferred_key in self.keys:
                    cand = self.keys[preferred_key]
                    self._reset_daily_if_needed(cand)
                    now = time.time()
                    if (
                        cand.is_valid
                        and now >= cand.cooldown_until
                        and cand.daily_count < MAX_DAILY_REQUESTS
                    ):
                        state = cand

                if state is None:
                    state = self._select_best_key()

                if state is not None:
                    now = time.time()
                    elapsed = now - state.last_request
                    sleep_for = max(0.0, MIN_REQUEST_INTERVAL - elapsed)

                    state.last_request = now + sleep_for
                    state.daily_count += 1
                    chosen_key = state.key
                    client = state.client

                    if sleep_for <= 0:
                        return client, chosen_key
                else:
                    sleep_for = -1

            if sleep_for > 0:
                time.sleep(sleep_for)
                return client, chosen_key

            if time.time() - start > max_wait:
                raise RuntimeError(
                    "No available API key within timeout. "
                    "All keys are either rate-limited, in cooldown, or daily quota exhausted."
                )

            with self._lock:
                soonest = float("inf")
                for k in self._valid_keys:
                    s = self.keys[k]
                    self._reset_daily_if_needed(s)
                    if s.daily_count >= MAX_DAILY_REQUESTS:
                        soonest = min(soonest, s.daily_reset)
                    else:
                        soonest = min(soonest, max(s.cooldown_until, s.last_request + MIN_REQUEST_INTERVAL))

                wait = max(0.5, min(10.0, soonest - time.time()))
            time.sleep(wait)

    def report_rate_limit(self, key: str) -> None:
        with self._lock:
            if key not in self.keys:
                return
            state = self.keys[key]
            state.consecutive_429 += 1
            state.total_errors += 1
            extra = KEY_COOLDOWN_ON_429 * min(state.consecutive_429, 4)
            state.cooldown_until = time.time() + extra
            logger.warning(
                "Rate-limit hit on %s → cooldown %ds (consecutive=%d)",
                state.short, extra, state.consecutive_429,
            )

    def report_success(self, key: str) -> None:
        with self._lock:
            if key in self.keys:
                self.keys[key].consecutive_429 = 0

    def report_invalid(self, key: str) -> None:
        with self._lock:
            if key in self.keys:
                self.keys[key].is_valid = False
                self._valid_keys = [k for k, s in self.keys.items() if s.is_valid]
                logger.error("Key marked invalid: %s", self.keys[key].short)

    def available_count(self) -> int:
        with self._lock:
            now = time.time()
            n = 0
            for k in self._valid_keys:
                s = self.keys[k]
                self._reset_daily_if_needed(s)
                if now >= s.cooldown_until and s.daily_count < MAX_DAILY_REQUESTS:
                    n += 1
            return n

    def get_status(self) -> List[dict]:
        with self._lock:
            now = time.time()
            result = []
            for state in self.keys.values():
                self._reset_daily_if_needed(state)
                result.append({
                    "short": state.short,
                    "daily_count": state.daily_count,
                    "daily_limit": MAX_DAILY_REQUESTS,
                    "in_cooldown": now < state.cooldown_until,
                    "cooldown_left": max(0, int(state.cooldown_until - now)),
                    "is_valid": state.is_valid,
                    "consecutive_429": state.consecutive_429,
                    "total_errors": state.total_errors,
                })
            return result

def get_api_keys() -> List[str]:
    import os
    raw = (
        os.environ.get("GEMINI_API_KEYS")
        or os.environ.get("GOOGLE_API_KEYS")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    )
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError(
            "هیچ کلید Google/Gemini پیدا نشد.\n"
            "متغیر محیطی GEMINI_API_KEYS را تنظیم کنید (چند کلید را با کاما جدا کنید)."
        )
    logger.info("%d API key(s) loaded from environment", len(keys))
    return keys
