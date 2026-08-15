#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

class Theme:
    def __init__(self, dark: bool = True):
        self.dark = dark
        if dark:
            self.bg = "#0f1117"
            self.card_bg = "#1a1d27"
            self.surface = "#242836"
            self.surface_alt = "#2c3040"
            self.accent = "#6c8cff"
            self.accent_hover = "#8ba4ff"
            self.accent_muted = "#3d4f8a"
            self.text_primary = "#f0f2f8"
            self.text_secondary = "#9ba3b5"
            self.text_muted = "#6b7280"
            self.success = "#34d399"
            self.success_bg = "#0f2e24"
            self.warning = "#fbbf24"
            self.warning_bg = "#2e250f"
            self.error = "#f87171"
            self.error_bg = "#2e1515"
            self.border = "#2e3345"
            self.border_strong = "#3d4458"
            self.log_bg = "#0a0c12"
            self.log_fg = "#c8cdd8"
            self.entry_bg = "#1e222e"
            self.entry_fg = "#f0f2f8"
            self.entry_border = "#3d4458"
            self.progress_trough = "#1e222e"
            self.sidebar = "#14161f"
            self.header_bg = "#12141c"
        else:
            self.bg = "#f4f6fb"
            self.card_bg = "#ffffff"
            self.surface = "#eef1f8"
            self.surface_alt = "#e4e8f2"
            self.accent = "#4f6ef7"
            self.accent_hover = "#3b5bdb"
            self.accent_muted = "#c5d0ff"
            self.text_primary = "#1a1d27"
            self.text_secondary = "#5c6578"
            self.text_muted = "#8b93a7"
            self.success = "#059669"
            self.success_bg = "#d1fae5"
            self.warning = "#d97706"
            self.warning_bg = "#fef3c7"
            self.error = "#dc2626"
            self.error_bg = "#fee2e2"
            self.border = "#e2e6ef"
            self.border_strong = "#c8cfe0"
            self.log_bg = "#1a1d27"
            self.log_fg = "#d1d5e0"
            self.entry_bg = "#ffffff"
            self.entry_fg = "#1a1d27"
            self.entry_border = "#c8cfe0"
            self.progress_trough = "#e2e6ef"
            self.sidebar = "#eef1f8"
            self.header_bg = "#ffffff"

        self.font_family = "Tahoma"
        self.font_mono = "Consolas"
        self.font_ui = "Segoe UI"

def apply_theme(root: tk.Tk, theme: Theme) -> None:
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    f = theme.font_family

    style.configure(".", background=theme.bg, foreground=theme.text_primary, font=(f, 10))
    style.configure("TFrame", background=theme.bg)
    style.configure("Card.TFrame", background=theme.card_bg)
    style.configure("Surface.TFrame", background=theme.surface)
    style.configure("Header.TFrame", background=theme.header_bg)
    style.configure("Sidebar.TFrame", background=theme.sidebar)
    style.configure("Metric.TFrame", background=theme.surface)

    style.configure("TLabel", background=theme.bg, foreground=theme.text_primary, font=(f, 10))
    style.configure("Title.TLabel", background=theme.header_bg, foreground=theme.text_primary, font=(f, 18, "bold"))
    style.configure("Subtitle.TLabel", background=theme.header_bg, foreground=theme.text_secondary, font=(f, 9))
    style.configure("Card.TLabel", background=theme.card_bg, foreground=theme.text_primary, font=(f, 10))
    style.configure("CardTitle.TLabel", background=theme.card_bg, foreground=theme.text_primary, font=(f, 11, "bold"))
    style.configure("Status.TLabel", background=theme.bg, foreground=theme.text_secondary, font=(f, 9))
    style.configure("Success.TLabel", background=theme.bg, foreground=theme.success, font=(f, 9, "bold"))
    style.configure("Error.TLabel", background=theme.bg, foreground=theme.error, font=(f, 9, "bold"))
    style.configure("Warning.TLabel", background=theme.bg, foreground=theme.warning, font=(f, 9, "bold"))
    style.configure("MetricValue.TLabel", background=theme.surface, foreground=theme.text_primary, font=(f, 16, "bold"))
    style.configure("MetricLabel.TLabel", background=theme.surface, foreground=theme.text_secondary, font=(f, 8))
    style.configure("Footer.TLabel", background=theme.bg, foreground=theme.text_muted, font=(f, 8))
    style.configure("Accent.TLabel", background=theme.bg, foreground=theme.accent, font=(f, 10, "bold"))

    style.configure(
        "Accent.TButton",
        font=(f, 10, "bold"),
        padding=(18, 9),
        background=theme.accent,
        foreground="#ffffff",
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme.accent_hover), ("!disabled", theme.accent), ("disabled", theme.border)],
        foreground=[("!disabled", "#ffffff"), ("disabled", theme.text_muted)],
    )

    style.configure(
        "Secondary.TButton",
        font=(f, 9),
        padding=(14, 7),
        background=theme.surface,
        foreground=theme.text_primary,
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", theme.surface_alt), ("!disabled", theme.surface), ("disabled", theme.border)],
        foreground=[("!disabled", theme.text_primary), ("disabled", theme.text_muted)],
    )

    style.configure(
        "Danger.TButton",
        font=(f, 9),
        padding=(14, 7),
        background=theme.error_bg,
        foreground=theme.error,
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", theme.error), ("!disabled", theme.error_bg)],
        foreground=[("active", "#ffffff"), ("!disabled", theme.error)],
    )

    style.configure(
        "Ghost.TButton",
        font=(f, 9),
        padding=(10, 6),
        background=theme.header_bg,
        foreground=theme.text_secondary,
        borderwidth=0,
    )
    style.map(
        "Ghost.TButton",
        background=[("active", theme.surface), ("!disabled", theme.header_bg)],
        foreground=[("active", theme.text_primary), ("!disabled", theme.text_secondary)],
    )

    style.configure("TLabelframe", background=theme.card_bg, foreground=theme.text_primary, borderwidth=1, relief="flat")
    style.configure(
        "TLabelframe.Label",
        background=theme.card_bg,
        foreground=theme.accent,
        font=(f, 10, "bold"),
    )

    style.configure(
        "TEntry",
        font=(f, 11),
        padding=8,
        fieldbackground=theme.entry_bg,
        foreground=theme.entry_fg,
        borderwidth=1,
        relief="flat",
    )
    style.map("TEntry", fieldbackground=[("focus", theme.entry_bg)], bordercolor=[("focus", theme.accent)])

    style.configure("TCombobox", font=(f, 10), padding=5)
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=theme.progress_trough,
        background=theme.accent,
        thickness=10,
        borderwidth=0,
        lightcolor=theme.accent,
        darkcolor=theme.accent,
    )

    style.configure(
        "Treeview",
        background=theme.card_bg,
        foreground=theme.text_primary,
        fieldbackground=theme.card_bg,
        font=(f, 9),
        rowheight=28,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        font=(f, 9, "bold"),
        background=theme.surface,
        foreground=theme.text_secondary,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", theme.accent_muted)],
        foreground=[("selected", theme.text_primary)],
    )
    style.map("Treeview.Heading", background=[("active", theme.surface_alt)])

    style.configure("TNotebook", background=theme.bg, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        font=(f, 10),
        padding=(16, 8),
        background=theme.surface,
        foreground=theme.text_secondary,
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", theme.card_bg), ("active", theme.surface_alt)],
        foreground=[("selected", theme.accent), ("active", theme.text_primary)],
    )

    style.configure("TSeparator", background=theme.border)
    style.configure("TScrollbar", background=theme.surface, troughcolor=theme.bg, borderwidth=0, arrowsize=12)
    style.map("TScrollbar", background=[("active", theme.border_strong), ("!disabled", theme.surface)])
