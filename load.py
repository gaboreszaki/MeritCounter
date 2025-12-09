"""
EDMC Merit Counter.

A plugin for track Powerplay 2.0 progress directly from the EDMC interface
"""

# Import UI elements
import tkinter as tk
import myNotebook as nb

# import plugin
import merit_counter

mc = merit_counter.MeritCounter()


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
        mc.handle_powerplay_event(entry)

    elif entry['event'] == 'PowerplayMerits':
        mc.handle_merits_event(entry)

    elif entry['event'] == 'PowerplayRank':
        mc.handle_rank_event(entry)
