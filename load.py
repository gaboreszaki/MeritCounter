"""
Example EDMC plugin.

It adds a single button to the EDMC interface that displays the number of times it has been clicked.
"""
from __future__ import annotations

import logging
import tkinter as tk
from theme import theme

import os

import myNotebook as nb  # noqa: N813
from ttkHyperlinkLabel import HyperlinkLabel
from config import appname, config

plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f"{appname}.{plugin_name}")


class MeritCounter:
    def __init__(self) -> None:

        self.power_name = tk.StringVar(value=str(config.get_str('mc_power_name') or "No Power"))
        self.power_rank = tk.StringVar(value=str(config.get_int('mc_power_rank') or "0"))
        self.merit_total = tk.StringVar(value=str(config.get_int('mc_merit_total') or "0"))

        # Session
        self.merit_session = tk.StringVar(value="0")
        self.merit_session_int = 0
        self.last_income = tk.StringVar(value="0")

        # Merits to the next level
        self.merit_missing = tk.StringVar(value="0")
        self.update_missing_merits()

        # Display Preferences
        # def get_cfg(key: str) -> bool:
        #     val = config.get_int(key)
        #     return val if val is not None else True

        self.show_power_name = tk.BooleanVar(value=config.get_int('mc_show_power_name') or 1)
        self.show_power_rank = tk.BooleanVar(value=config.get_int('mc_show_power_rank') or 1)
        self.show_merit_total = tk.BooleanVar(value=config.get_int('mc_show_merit_total') or 1)
        self.show_merit_missing = tk.BooleanVar(value=config.get_int('mc_show_merit_missing') or 1)
        self.show_merit_session = tk.BooleanVar(value=config.get_int('mc_show_merit_session') or 1)
        self.show_last_income = tk.BooleanVar(value=config.get_int('mc_show_last_income') or 1)

        logger.info("MeritCounter instantiated")

    def on_load(self) -> str:
        return plugin_name

    def on_unload(self) -> None:
        self.on_preferences_closed("", False)  # Save our prefs

    def setup_preferences(self, parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:

        PADX = 10  # noqa: N806
        BUTTONX = 12  # noqa: N806
        PADY = 1  # noqa: N806
        BOXY = 2  # noqa: N806
        SEPY = 10  # noqa: N806

        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        current_row = 0

        HyperlinkLabel(
            frame,
            text='MeritCounter',
            background=nb.Label().cget('background'),
            url='https://github.com/gaboreszaki/MeritCounter',
            underline=True
        ).grid(row=current_row, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)
        current_row += 1


        nb.Checkbutton(frame, text="Show ", variable=self.show_power_name).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Power Name').grid(row=current_row, padx=PADX, pady=PADY, column=1, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.power_name).grid(row=current_row, padx=PADX, pady=BOXY, column=2, sticky=tk.EW)
        current_row += 1

        nb.Checkbutton(frame, text="Show ", variable=self.show_power_rank).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Power Level').grid(row=current_row, column=1, padx=PADX, pady=PADY, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.power_rank).grid(row=current_row, padx=PADX, pady=BOXY, column=2, sticky=tk.EW)
        current_row += 1

        nb.Checkbutton(frame, text="Show ", variable=self.show_merit_total).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Total Merits').grid(row=current_row, column=1, padx=PADX, pady=PADY, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.merit_total).grid(row=current_row, padx=PADX, pady=BOXY, column=2, sticky=tk.W)
        current_row += 1

        nb.Checkbutton(frame, text="Show ", variable=self.show_merit_missing).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Missing Merits').grid(row=current_row, column=1, padx=PADX, pady=PADY, sticky=tk.W)
        current_row += 1

        nb.Checkbutton(frame, text="Show ", variable=self.show_merit_session).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Session Merits').grid(row=current_row, column=1, padx=PADX, pady=PADY, sticky=tk.W)
        current_row += 1

        nb.Checkbutton(frame, text="Show ", variable=self.show_last_income).grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.Label(frame, text='Last income').grid(row=current_row, column=1, padx=PADX, pady=PADY, sticky=tk.W)
        current_row += 1

        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        config.set('mc_power_name', str(self.power_name.get()))
        config.set('mc_power_rank', int(self.power_rank.get()))
        config.set('mc_total_merits', int(self.merit_total.get()))

        config.set('mc_show_power_name', int(self.show_power_name.get()))
        config.set('mc_show_power_rank', int(self.show_power_rank.get()))
        config.set('mc_show_merit_total', int(self.show_merit_total.get()))
        config.set('mc_show_merit_missing', int(self.show_merit_missing.get()))
        config.set('mc_show_merit_session', int(self.show_merit_session.get()))
        config.set('mc_show_last_income', int(self.show_last_income.get()))

        self.update_missing_merits()
        self.draw_ui()

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        self.frame = tk.Frame(parent)
        self.draw_ui()
        return self.frame

    def draw_ui(self) -> None:
        if not hasattr(self, 'frame') or not self.frame or not self.frame.winfo_exists():
            return

        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()

        current_row = 0

        tk.Label(self.frame, text="//// Merit Counter", font=("Arial", 12, "bold"), fg="white").grid(row=current_row, sticky=tk.W)
        tk.Label(self.frame, text="(PowerPLay 2.0)", font=("Arial", 8)).grid(row=current_row, column=1, sticky=tk.W)

        current_row += 1

        if self.show_power_name.get():
            tk.Label(self.frame, text="Power Name:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.power_name, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_power_rank.get():
            tk.Label(self.frame, text="Power Rank:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.power_rank, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_total.get():
            tk.Label(self.frame, text="Current Merits:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_total, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_missing.get():
            tk.Label(self.frame, text="Merits to next level:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_missing, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_session.get():
            tk.Label(self.frame, text="Session Total:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_session, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_last_income.get():
            tk.Label(self.frame, text="Last Merit Income:").grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.last_income, fg="white").grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        theme.update(self.frame)

    def update_missing_merits(self) -> None:
        try:
            level = int(self.power_rank.get())
            total = int(self.merit_total.get())
        except ValueError:
            return

        next_level = level + 1

        base_thresholds = {2: 2000, 3: 5000, 4: 9000, 5: 15000}

        if next_level in base_thresholds:
            target = base_thresholds[next_level]
        elif next_level > 5:
            target = 15000 + (next_level - 5) * 8000
        else:
            target = 0

        missing = max(0, target - total)
        self.merit_missing.set(str(missing))


mc = MeritCounter()


def plugin_start3(plugin_dir: str) -> str:
    return mc.on_load()


def plugin_stop() -> None:
    return mc.on_unload()


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:
    return mc.setup_preferences(parent, cmdr, is_beta)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    return mc.on_preferences_closed(cmdr, is_beta)


def plugin_app(parent: tk.Frame) -> tk.Frame | None:
    return mc.setup_main_ui(parent)


def journal_entry(cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> None:
    if entry['event'] == 'Powerplay':
        config.set('mc_power_name', str(entry['Power']))
        config.set('mc_power_rank', int(entry['Rank']))
        config.set('mc_merit_total', int(entry['Merits']))

        mc.power_name.set(str(entry['Power']))
        mc.power_rank.set(str(entry['Rank']))
        mc.merit_total.set(str(entry['Merits']))

        mc.update_missing_merits()

    if entry['event'] == 'PowerplayMerits':
        config.set('mc_merit_total', int(entry['TotalMerits']))

        mc.merit_total.set(str(entry['TotalMerits']))
        mc.update_missing_merits()

        mc.merit_session_int += int(entry['MeritsGained'])
        mc.merit_session.set(str(mc.merit_session_int))

        mc.last_income.set(str(entry['MeritsGained']))

    if entry['event'] == 'PowerplayRank':
        config.set('mc_power_rank', int(entry['Rank']))
        mc.power_rank.set(str(entry['Rank']))
        mc.update_missing_merits()
