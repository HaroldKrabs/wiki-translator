#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from logger_setup import setup_logger
from config import LOG_FILE

def main():
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("شروع برنامه ربات ترجمه ویکی‌پدیا v5.1")
    logger.info("فایل لاگ: %s", LOG_FILE)
    logger.info("=" * 60)

    import tkinter as tk
    from ui.app import TranslatorApp

    root = tk.Tk()
    try:
        root.option_add("*Font", "Tahoma 10")
    except Exception:
        pass

    TranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
