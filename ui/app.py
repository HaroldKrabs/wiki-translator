#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import queue
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict, List, Optional, Tuple

from config import (
    BASE_DIR,
    DEFAULT_MAX_ARTICLES,
    INPUT_DIR,
    LIST_FILE_NAME,
    LOG_FILE,
    MODEL_NAME,
    OUTPUT_DIR,
    PROGRESS_DIR,
    WARNINGS_FILE,
)
from key_manager import KeyManager, get_api_keys
from logger_setup import get_logger, log_exception
from translator_core import process_article
from utils import persian_sort_key, safe_filename
from wikipedia_api import fetch_category_members, filter_without_persian
from .styles import Theme, apply_theme

logger = get_logger()

class TranslatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ربات ترجمه مقالات ویکی‌پدیا  •  v5.1")
        self.root.geometry("1100x820")
        self.root.minsize(920, 680)

        self.theme = Theme(dark=True)
        self.log_queue: queue.Queue = queue.Queue()
        self.is_running = False
        self.is_paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[Future, str] = {}

        self.total_to_do = 0
        self.success_count = 0
        self.fail_count = 0
        self.flagged_count = 0

        apply_theme(self.root, self.theme)
        self.root.configure(bg=self.theme.bg)

        self._build_ui()
        self._poll_log()
        self._poll_key_status()

        logger.info("UI started. Log file: %s", LOG_FILE)

    def _build_ui(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 16, 24, 12))
        header.pack(fill=tk.X)

        title_row = ttk.Frame(header, style="Header.TFrame")
        title_row.pack(fill=tk.X)

        left_title = ttk.Frame(title_row, style="Header.TFrame")
        left_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left_title, text="ترجمه مقالات ویکی‌پدیا به فارسی", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            left_title,
            text="رده انگلیسی → فیلتر بدون نسخه فارسی → ترجمه هوشمند بخش‌محور → خروجی مرتب‌شده",
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))

        right_header = ttk.Frame(title_row, style="Header.TFrame")
        right_header.pack(side=tk.RIGHT)

        self.theme_btn = ttk.Button(right_header, text="☀️", width=3, style="Ghost.TButton", command=self._toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=(8, 0))

        model_badge = ttk.Label(right_header, text=f"  {MODEL_NAME}  ", style="Accent.TLabel")
        model_badge.pack(side=tk.RIGHT, padx=(0, 4))

        sep = ttk.Separator(self.root, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X)

        body = ttk.Frame(self.root, padding=(20, 14, 20, 8))
        body.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(body)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        control = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(control, text="  ▶  کنترل و اجرا  ")

        settings = ttk.LabelFrame(control, text="  تنظیمات ترجمه  ", padding=16)
        settings.pack(fill=tk.X, pady=(0, 14))

        row1 = ttk.Frame(settings)
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="نام رده انگلیسی", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="Physics")
        self.category_entry = ttk.Entry(row1, textvariable=self.category_var, font=("Tahoma", 11))
        self.category_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.category_entry.bind("<Control-v>", self._paste_into_entry)
        self.category_entry.bind("<Control-V>", self._paste_into_entry)

        row2 = ttk.Frame(settings)
        row2.pack(fill=tk.X, pady=6)
        ttk.Label(row2, text="حداکثر مقاله", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        self.max_var = tk.StringVar(value=str(DEFAULT_MAX_ARTICLES))
        max_entry = ttk.Entry(row2, textvariable=self.max_var, width=12)
        max_entry.pack(side=tk.LEFT)
        ttk.Label(row2, text="  برای جلوگیری از رده‌های بسیار بزرگ", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=8)

        metrics = ttk.Frame(control)
        metrics.pack(fill=tk.X, pady=(0, 14))

        self._metric_cards = []
        metric_defs = [
            ("موفق", "success_count", "success"),
            ("ناموفق", "fail_count", "error"),
            ("بازبینی", "flagged_count", "warning"),
            ("باقی‌مانده", "remaining", "accent"),
        ]
        for i, (label, key, kind) in enumerate(metric_defs):
            card = ttk.Frame(metrics, style="Metric.TFrame", padding=(14, 10))
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0 if i == 0 else 8, 0))
            val_lbl = ttk.Label(card, text="0", style="MetricValue.TLabel")
            val_lbl.pack(anchor=tk.W)
            ttk.Label(card, text=label, style="MetricLabel.TLabel").pack(anchor=tk.W)
            self._metric_cards.append((key, val_lbl))

        btn_frame = ttk.Frame(control)
        btn_frame.pack(fill=tk.X, pady=(0, 14))

        self.start_btn = ttk.Button(btn_frame, text="▶   شروع ترجمه", style="Accent.TButton", command=self.start_translation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.pause_btn = ttk.Button(btn_frame, text="⏸  توقف موقت", style="Secondary.TButton", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(btn_frame, text="⏹  توقف کامل", style="Danger.TButton", command=self.request_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Frame(btn_frame).pack(side=tk.LEFT, expand=True)

        self.open_out_btn = ttk.Button(btn_frame, text="📂  پوشه خروجی", style="Secondary.TButton", command=self.open_output_folder)
        self.open_out_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.open_log_btn = ttk.Button(btn_frame, text="📄  فایل لاگ", style="Secondary.TButton", command=self.open_log_file)
        self.open_log_btn.pack(side=tk.LEFT)

        prog_frame = ttk.LabelFrame(control, text="  پیشرفت زنده  ", padding=14)
        prog_frame.pack(fill=tk.X, pady=(0, 8))

        status_row = ttk.Frame(prog_frame)
        status_row.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="آماده برای شروع")
        ttk.Label(status_row, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)
        self.pct_var = tk.StringVar(value="0%")
        ttk.Label(status_row, textvariable=self.pct_var, style="Accent.TLabel").pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, pady=(10, 6))

        self.stats_var = tk.StringVar(value="")
        ttk.Label(prog_frame, textvariable=self.stats_var, style="Subtitle.TLabel").pack(anchor=tk.W)

        articles_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(articles_tab, text="  📑  مقالات  ")

        tree_frame = ttk.Frame(articles_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("status", "english", "persian")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        self.tree.heading("status", text="وضعیت")
        self.tree.heading("english", text="عنوان انگلیسی")
        self.tree.heading("persian", text="عنوان فارسی")
        self.tree.column("status", width=100, anchor=tk.CENTER, stretch=False)
        self.tree.column("english", width=360)
        self.tree.column("persian", width=360)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("ok", foreground="#34d399")
        self.tree.tag_configure("fail", foreground="#f87171")
        self.tree.tag_configure("queue", foreground="#9ba3b5")
        self.tree.tag_configure("work", foreground="#6c8cff")

        keys_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(keys_tab, text="  🔑  کلیدهای API  ")

        keys_header = ttk.Frame(keys_tab)
        keys_header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(keys_header, text="وضعیت زنده کلیدهای Gemini", style="CardTitle.TLabel").pack(side=tk.LEFT)
        self.keys_refresh_lbl = ttk.Label(keys_header, text="", style="Subtitle.TLabel")
        self.keys_refresh_lbl.pack(side=tk.RIGHT)

        self.keys_tree = ttk.Treeview(
            keys_tab,
            columns=("key", "usage", "cooldown", "status"),
            show="headings",
            height=12,
        )
        self.keys_tree.heading("key", text="کلید")
        self.keys_tree.heading("usage", text="استفاده روزانه")
        self.keys_tree.heading("cooldown", text="کول‌داون")
        self.keys_tree.heading("status", text="وضعیت")
        self.keys_tree.column("key", width=160)
        self.keys_tree.column("usage", width=150)
        self.keys_tree.column("cooldown", width=110)
        self.keys_tree.column("status", width=140)
        self.keys_tree.pack(fill=tk.BOTH, expand=True)

        log_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(log_tab, text="  📋  گزارش‌ها  ")

        log_toolbar = ttk.Frame(log_tab)
        log_toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(log_toolbar, text="لاگ زنده پردازش", style="CardTitle.TLabel").pack(side=tk.LEFT)
        ttk.Button(log_toolbar, text="پاک کردن", style="Ghost.TButton", command=self._clear_log).pack(side=tk.RIGHT)

        self.log_text = scrolledtext.ScrolledText(
            log_tab,
            height=24,
            font=("Consolas", 9),
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg=self.theme.log_bg,
            fg=self.theme.log_fg,
            insertbackground="#ffffff",
            selectbackground="#3d4f8a",
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(self.root, padding=(24, 6, 24, 12))
        footer.pack(fill=tk.X)
        ttk.Label(
            footer,
            text="خروجی: translated/نام‌رده/   •   لیست مرتب‌شده: 0010010.txt   •   لاگ: logs/translator.log   •   v5.1",
            style="Footer.TLabel",
        ).pack(anchor=tk.W)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _paste_into_entry(self, event=None):
        try:
            clipboard = self.root.clipboard_get()
            if clipboard:
                try:
                    self.category_entry.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                self.category_entry.insert(tk.INSERT, clipboard)
        except tk.TclError:
            pass
        return "break"

    def _toggle_theme(self):
        self.theme = Theme(dark=not self.theme.dark)
        apply_theme(self.root, self.theme)
        self.root.configure(bg=self.theme.bg)
        self.log_text.configure(bg=self.theme.log_bg, fg=self.theme.log_fg)
        self.theme_btn.configure(text="☀️" if self.theme.dark else "🌙")
        self.tree.tag_configure("ok", foreground=self.theme.success)
        self.tree.tag_configure("fail", foreground=self.theme.error)
        self.tree.tag_configure("queue", foreground=self.theme.text_secondary)
        self.tree.tag_configure("work", foreground=self.theme.accent)

    def log(self, message: str):
        self.log_queue.put(message)

    def _poll_log(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(120, self._poll_log)

    def _poll_key_status(self):
        self.root.after(2000, self._poll_key_status)

    def _update_stats(self):
        remaining = max(0, self.total_to_do - self.success_count - self.fail_count)
        values = {
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "flagged_count": self.flagged_count,
            "remaining": remaining,
        }
        for key, lbl in self._metric_cards:
            lbl.configure(text=str(values.get(key, 0)))

        if self.total_to_do > 0:
            done = self.success_count + self.fail_count
            pct = int(100 * done / self.total_to_do)
            self.progress["value"] = pct
            self.pct_var.set(f"{pct}%")
            self.stats_var.set(f"{done} از {self.total_to_do} مقاله پردازش شده")
        else:
            self.progress["value"] = 0
            self.pct_var.set("0%")
            self.stats_var.set("")

    def _set_article_status(self, english: str, status: str, persian: str = ""):
        tag = "queue"
        if "موفق" in status or "✓" in status:
            tag = "ok"
        elif "خطا" in status or "✗" in status:
            tag = "fail"
        elif "ترجمه" in status:
            tag = "work"

        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if vals and vals[1] == english:
                self.tree.item(item, values=(status, english, persian or vals[2]), tags=(tag,))
                return
        self.tree.insert("", tk.END, values=(status, english, persian), tags=(tag,))

    def open_log_file(self):
        try:
            path = str(LOG_FILE)
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showinfo("مسیر لاگ", f"فایل لاگ:\n{LOG_FILE}\n\n{e}")

    def open_output_folder(self):
        try:
            path = str(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showinfo("پوشه خروجی", f"{OUTPUT_DIR}\n\n{e}")

    def toggle_pause(self):
        if not self.is_running:
            return
        if self.is_paused:
            self.is_paused = False
            self._pause_event.set()
            self.pause_btn.configure(text="⏸  توقف موقت")
            self.status_var.set("در حال ادامه...")
            self.log("▶ ادامه کار")
        else:
            self.is_paused = True
            self._pause_event.clear()
            self.pause_btn.configure(text="▶  ادامه")
            self.status_var.set("متوقف موقت")
            self.log("⏸ توقف موقت")

    def request_stop(self):
        if not self.is_running:
            return
        if messagebox.askyesno("توقف", "آیا مطمئن هستید که می‌خواهید ترجمه را متوقف کنید؟"):
            self._stop_requested = True
            self._pause_event.set()
            self.status_var.set("در حال توقف...")
            self.log("⏹ درخواست توقف ارسال شد")

    def start_translation(self):
        if self.is_running:
            messagebox.showwarning("در حال اجرا", "یک فرآیند ترجمه در حال اجراست.")
            return

        category = self.category_var.get().strip()
        if not category:
            messagebox.showwarning("خالی", "نام رده را وارد کنید.")
            return

        try:
            max_articles = int(self.max_var.get().strip())
            if max_articles < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("مقدار نامعتبر", "حداکثر مقاله باید عدد مثبت باشد.")
            return

        try:
            api_keys = get_api_keys()
        except RuntimeError as e:
            messagebox.showerror("خطای کلید API", str(e))
            logger.error("No API keys: %s", e)
            return

        self.is_running = True
        self.is_paused = False
        self._stop_requested = False
        self._pause_event.set()
        self.success_count = 0
        self.fail_count = 0
        self.flagged_count = 0
        self.total_to_do = 0
        self.progress["value"] = 0
        self._update_stats()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_var.set("در حال کار...")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_translation,
            args=(category, max_articles, api_keys),
            daemon=True,
        )
        thread.start()

    def _run_translation(self, category: str, max_articles: int, api_keys: List[str]):
        try:
            for d in (INPUT_DIR, OUTPUT_DIR, PROGRESS_DIR):
                d.mkdir(parents=True, exist_ok=True)

            safe_cat = safe_filename(category)
            category_folder = OUTPUT_DIR / safe_cat
            category_folder.mkdir(parents=True, exist_ok=True)

            key_manager = KeyManager(api_keys)
            workers = min(3, len(api_keys))

            self.log(
                f"رده: {category} | حداکثر: {max_articles} | کلیدها: {len(api_keys)} | "
                f"worker: {workers} | مدل: {MODEL_NAME}"
            )
            self.log(f"پوشه خروجی: {category_folder.relative_to(BASE_DIR)}")

            self.root.after(0, lambda: self._refresh_keys_ui(key_manager))

            self.log("در حال دریافت لیست مقالات رده...")
            try:
                all_titles = fetch_category_members(category, max_articles)
            except Exception as e:
                self.log(f"خطا در دریافت اعضای رده: {e}")
                log_exception(logger, "fetch_category_members")
                self.status_var.set("خطا در دریافت رده")
                return

            self.log(f"{len(all_titles)} مقاله در رده پیدا شد.")
            if not all_titles:
                self.log("هیچ مقاله‌ای در این رده یافت نشد.")
                self.status_var.set("خالی")
                return

            self.log("بررسی وجود نسخه فارسی...")
            try:
                titles_to_translate = filter_without_persian(all_titles, self.log)
            except Exception as e:
                self.log(f"خطا در فیلتر کردن مقالات: {e}")
                log_exception(logger, "filter_without_persian")
                self.status_var.set("خطا در بررسی فارسی")
                return

            self.log(f"{len(titles_to_translate)} مقاله بدون نسخه فارسی انتخاب شد.")
            if not titles_to_translate:
                self.log("همه مقالات این رده نسخه فارسی دارند.")
                self.status_var.set("تمام — چیزی برای ترجمه نبود")
                return

            self.total_to_do = len(titles_to_translate)
            self.root.after(0, self._update_stats)

            for t in titles_to_translate:
                self.root.after(0, lambda title=t: self._set_article_status(title, "در صف", ""))

            all_flagged: List[str] = []
            title_pairs: List[Tuple[str, str]] = []

            with ThreadPoolExecutor(max_workers=workers) as executor:
                self._executor = executor
                futures = {}
                for idx, title in enumerate(titles_to_translate):
                    if self._stop_requested:
                        break
                    key = api_keys[idx % len(api_keys)]
                    fut = executor.submit(
                        self._wrapped_process,
                        key_manager,
                        key,
                        title,
                        category_folder,
                    )
                    futures[fut] = title
                    self.root.after(0, lambda t=title: self._set_article_status(t, "در حال ترجمه", ""))

                for future in as_completed(futures):
                    if self._stop_requested:
                        break
                    title = futures[future]
                    try:
                        persian_title, flagged = future.result()
                        if persian_title:
                            title_pairs.append((persian_title, title))
                        all_flagged.extend(flagged)
                        self.success_count += 1
                        self.flagged_count += len(flagged)
                        self.log(f"✓ تمام شد: {title}  →  {persian_title}")
                        self.root.after(
                            0,
                            lambda t=title, p=persian_title: self._set_article_status(t, "✓ موفق", p),
                        )
                    except Exception as e:
                        self.fail_count += 1
                        self.log(f"✗ خطا در «{title}»: {e}")
                        log_exception(logger, f"Processing {title}")
                        self.root.after(0, lambda t=title: self._set_article_status(t, "✗ خطا", ""))

                    self.root.after(0, self._update_stats)
                    self.root.after(0, lambda: self._refresh_keys_ui(key_manager))

            list_path = category_folder / LIST_FILE_NAME
            try:
                sorted_pairs = sorted(title_pairs, key=lambda p: persian_sort_key(p[0]))
                lines = [
                    f"# [[{fa}]]  —  [[:en:{en}]]"
                    for fa, en in sorted_pairs
                ]
                list_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
                self.log(
                    f"فایل لیست (مرتب‌شده الفبایی فارسی + لینک انگلیسی) ذخیره شد: "
                    f"{list_path.relative_to(BASE_DIR)}  ({len(sorted_pairs)} عنوان)"
                )
            except Exception as e:
                self.log(f"خطا در نوشتن فایل لیست: {e}")
                logger.warning("Could not write 0010010.txt: %s", e)

            if all_flagged:
                try:
                    WARNINGS_FILE.write_text(
                        "تکه‌های نیازمند بازبینی دستی:\n\n" + "\n".join(all_flagged),
                        encoding="utf-8",
                    )
                    self.log(f"{len(all_flagged)} تکه نیاز به بازبینی دارند → {WARNINGS_FILE.name}")
                except Exception as e:
                    logger.warning("Could not write warnings: %s", e)

            summary = (
                f"پایان | موفق: {self.success_count} | ناموفق: {self.fail_count} | "
                f"انتخاب‌شده: {len(titles_to_translate)} | بازبینی: {len(all_flagged)}"
            )
            self.log(summary)
            if self._stop_requested:
                self.status_var.set(f"متوقف شد — موفق: {self.success_count} | ناموفق: {self.fail_count}")
            else:
                self.status_var.set(f"تمام شد — موفق: {self.success_count} | ناموفق: {self.fail_count}")

        except Exception as e:
            self.log(f"خطای کلی برنامه: {e}")
            log_exception(logger, "_run_translation")
            self.status_var.set("خطا")
        finally:
            self.is_running = False
            self._executor = None
            self.root.after(0, lambda: self.start_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.pause_btn.configure(state=tk.DISABLED, text="⏸  توقف موقت"))
            self.root.after(0, lambda: self.stop_btn.configure(state=tk.DISABLED))

    def _wrapped_process(self, key_manager, key, title, category_folder):
        while not self._pause_event.is_set():
            if self._stop_requested:
                raise RuntimeError("Stopped by user")
            time.sleep(0.3)
        if self._stop_requested:
            raise RuntimeError("Stopped by user")
        return process_article(key_manager, key, title, category_folder, self.log)

    def _refresh_keys_ui(self, key_manager: KeyManager):
        for item in self.keys_tree.get_children():
            self.keys_tree.delete(item)
        try:
            for st in key_manager.get_status():
                status = "معتبر" if st["is_valid"] else "نامعتبر"
                if st["in_cooldown"]:
                    status = f"کول‌داون {st['cooldown_left']}s"
                usage = f"{st['daily_count']} / {st['daily_limit']}"
                self.keys_tree.insert("", tk.END, values=(st["short"], usage, st["cooldown_left"], status))
            self.keys_refresh_lbl.configure(text="به‌روز شد")
        except Exception:
            pass
