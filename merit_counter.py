# Import standard library components
import os
import math
import logging
from typing import Optional

# import configs, constants and worker thread
from config import appname, config
import mc_constants as const
from UpdateCheckerThreaded import UpdateChecker  # Import the new class

# Import UI elements
import tkinter as tk
import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from theme import theme


plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f"{appname}.{plugin_name}")

# Configuration
PLUGIN_VERSION = "1.0.4"
GITHUB_REPO = "gaboreszaki/MeritCounter"


class MeritCounter:
    def __init__(self) -> None:

        self.power_name = tk.StringVar(value=str(config.get_str('mc_power_name') or "No Power"))
        self.power_rank = tk.StringVar(value=str(config.get_int('mc_power_rank') or "0"))
        self.merit_total = tk.StringVar(value=str(config.get_int('mc_merits_total') or "0"))

        # Session
        self.merit_session = tk.StringVar(value="0")
        self.merit_session_int = 0
        self.last_income = tk.StringVar(value="0")

        # Merits to the next level
        self.merit_missing = tk.StringVar(value="0")
        self.update_missing_merits()

        # Display preferences
        self.show_power_name = tk.BooleanVar(value=config.get_int('mc_show_power_name') or 1)
        self.show_power_rank = tk.BooleanVar(value=config.get_int('mc_show_power_rank') or 1)
        self.show_merit_total = tk.BooleanVar(value=config.get_int('mc_show_merit_total') or 1)
        self.show_merit_missing = tk.BooleanVar(value=config.get_int('mc_show_merit_missing') or 1)
        self.show_merit_session = tk.BooleanVar(value=config.get_int('mc_show_merit_session') or 1)
        self.show_last_income = tk.BooleanVar(value=config.get_int('mc_show_last_income') or 1)

        # Update Checker Init
        self.updater = UpdateChecker(PLUGIN_VERSION, GITHUB_REPO)
        self.update_status_text = tk.StringVar(value=f"Current Version: v{PLUGIN_VERSION}")
        self.update_url = self.updater.release_url
        self.status_label = None

        self.frame = None
        self.text_color = None
        self.text_highlight = None
        self.hyperlink = None

        logger.info("MeritCounter instantiated")

    @staticmethod
    def on_load() -> str:
        return plugin_name

    def on_unload(self) -> None:
        self.on_preferences_closed("", False)  # Save our prefs

    # noinspection PyUnusedLocal
    def setup_preferences(self, parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[nb.Frame]:

        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        current_row = 0

        HyperlinkLabel(
            frame,
            text='MeritCounter',
            background=nb.Label().cget('background'),
            url='https://github.com/gaboreszaki/MeritCounter',
            underline=True
        ).grid(row=current_row, columnspan=2, padx=const.PAD_X, pady=const.PAD_Y, sticky=tk.W)
        current_row += 1

        # Define a helper to avoid repeating code
        def add_row(label_text, check_var, entry_var=None):
            nonlocal current_row
            nb.Checkbutton(frame, text="Show ", variable=check_var).grid(
                row=current_row, padx=const.PAD_X, pady=const.PAD_Y, sticky=tk.W
            )
            nb.Label(frame, text=label_text).grid(
                row=current_row, padx=const.PAD_X, pady=const.PAD_Y, column=1, sticky=tk.W
            )
            if entry_var:
                nb.EntryMenu(frame, textvariable=entry_var).grid(
                    row=current_row, padx=const.PAD_X, pady=const.BOX_Y, column=2, sticky=tk.EW
                )
            current_row += 1

        # Use the helper
        add_row('Power Name', self.show_power_name, self.power_name)
        add_row('Power Level', self.show_power_rank, self.power_rank)
        add_row('Total Merits', self.show_merit_total, self.merit_total)
        add_row('Missing Merits', self.show_merit_missing)
        add_row('Session Merits', self.show_merit_session)
        add_row('Last income', self.show_last_income)

        # --- Update Section ---
        current_row += 1
        tk.Frame(frame, height=2, bd=1, relief="sunken").grid(
            row=current_row, columnspan=3, sticky=tk.EW, padx=const.PAD_X, pady=5
        )
        current_row += 1

        nb.Button(frame, text="Check for Updates", command=self.start_update_check).grid(
            row=current_row, column=0, padx=const.PAD_X, pady=const.PAD_Y, sticky=tk.W
        )

        # Workaround: Use 'text' + trace instead of 'textvariable' to fix the cursor issue
        self.status_label = HyperlinkLabel(
            frame,
            text=self.update_status_text.get(),
            background=nb.Label().cget('background'),
            url=self.update_url,
            underline=False,
            cursor='hand2'
        )
        self.status_label.grid(row=current_row, column=1, columnspan=2, padx=const.PAD_X, pady=const.PAD_Y, sticky=tk.W)

        def update_ui_label(*_):
            if self.status_label.winfo_exists():
                self.status_label.configure(text=self.update_status_text.get())
                # Attempt to update URL if supported by the widget
                try:
                    self.status_label.configure(url=self.update_url)
                except (tk.TclError, AttributeError):
                    pass

        # Trace variable changes to update the label manually
        trace_id = self.update_status_text.trace_add("write", update_ui_label)

        # Cleanup trace when the widget is destroyed to prevent errors
        def on_destroy(_):
            try:
                self.update_status_text.trace_remove("write", trace_id)
            except tk.TclError:  # Catching specific TclError
                pass

        self.status_label.bind("<Destroy>", on_destroy)

        return frame

    def start_update_check(self) -> None:
        self.update_status_text.set("Checking...")
        self.updater.check(self._on_update_result)

    def _on_update_result(self, _is_new: bool, message: str, url: str) -> None:
        self.update_status_text.set(message)
        self.update_url = url

    # noinspection PyUnusedLocal
    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        config.set('mc_power_name', str(self.power_name.get()))
        config.set('mc_power_rank', int(self.power_rank.get()))
        config.set('mc_merits_total', int(self.merit_total.get()))

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

    def calculate_colors(self):

        if (config.get_int('theme') or 0) == theme.THEME_DEFAULT:
            self.text_color = "#636b74"
            self.text_highlight = "#000000"
            self.hyperlink = "orange"
        else:
            self.text_color = "#FF8000"
            self.text_highlight = "white"
            self.hyperlink = "blue"

    def draw_ui(self) -> None:
        if not hasattr(self, 'frame') or not self.frame or not self.frame.winfo_exists():
            return

        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.calculate_colors()
        current_row = 0

        ui_font = "Euro Caps"

        tk.Label(self.frame, text="Merit Counter", font=(ui_font, 14, "bold"), fg=self.text_highlight).grid(row=current_row, columnspan=2, sticky=tk.SW)
        tk.Label(self.frame, text=f"v{PLUGIN_VERSION}", fg=self.text_color, font=("Arial", 8)).grid(row=current_row, columnspan=2, sticky=tk.SE, pady=2)
        current_row += 1

        # tk.Label(self.frame, text="----- PowerPlay 2.0 -----", font=("Arial", 8), fg=self.text_highlight).grid(row=current_row, columnspan=2, sticky=tk.EW)
        current_row += 1

        if self.show_power_name.get():
            tk.Label(self.frame, text="Power Name:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.power_name, font=(ui_font, 10), fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_power_rank.get():
            tk.Label(self.frame, text="Power Rank:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.power_rank, fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_total.get():
            tk.Label(self.frame, text="Current Merits:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_total, fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_missing.get():
            tk.Label(self.frame, text="Merits to next level:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_missing, fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_merit_session.get():
            tk.Label(self.frame, text="Session Total:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.merit_session, fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        if self.show_last_income.get():
            tk.Label(self.frame, text="Last Merit Income:", fg=self.text_color).grid(row=current_row, sticky=tk.W)
            tk.Label(self.frame, textvariable=self.last_income, fg=self.text_highlight).grid(row=current_row, column=1, sticky=tk.W)
            current_row += 1

        theme.update(self.frame)

    def update_missing_merits(self) -> None:

        thresholds = const.POWER_LEVEL_THRESHOLDS
        required_merits = const.REQUIRED_MERITS_TO_NEXT_LEVEL

        try:
            level = int(self.power_rank.get())
            total = int(self.merit_total.get())
        except ValueError:
            return

        next_level = level + 1

        if next_level in thresholds:
            target = thresholds[next_level]
        elif next_level > 5:
            target = thresholds[5] + (next_level - 5) * required_merits
        else:
            target = 0

        missing = max(0, target - total)
        self.merit_missing.set(str(missing))

    def recalculate_current_power_rank(self) -> None:
        try:
            merit_total = int(self.merit_total.get() or 0)
            thresholds = const.POWER_LEVEL_THRESHOLDS
            required_merits = const.REQUIRED_MERITS_TO_NEXT_LEVEL

            if (thresholds[5] + required_merits) <= merit_total:
                tmp_rank = math.floor((merit_total - thresholds[5]) / required_merits) + 5

            elif thresholds[5] <= merit_total and merit_total > (thresholds[5] + required_merits):
                tmp_rank = 5
            elif thresholds[4] <= merit_total and merit_total > thresholds[5]:
                tmp_rank = 4
            elif thresholds[3] <= merit_total and merit_total > thresholds[4]:
                tmp_rank = 3
            elif thresholds[2] <= merit_total and merit_total > thresholds[3]:
                tmp_rank = 2
            elif thresholds[1] <= merit_total and merit_total > thresholds[2]:
                tmp_rank = 1
            else:
                tmp_rank = 0

            # Update both config and UI
            config.set('mc_power_rank', tmp_rank)
            self.power_rank.set(str(tmp_rank))

        except ValueError:
            return

    def handle_powerplay_event(self, entry: dict) -> None:
        power = str(entry['Power'])
        rank = int(entry['Rank'])
        merits = int(entry['Merits'])

        config.set('mc_power_name', power)
        config.set('mc_power_rank', rank)
        config.set('mc_merit_total', merits)

        self.power_name.set(power)
        self.power_rank.set(str(rank))
        self.merit_total.set(str(merits))

        self.update_missing_merits()

    def handle_merits_event(self, entry: dict) -> None:
        power = str(entry['Power'])
        total_merits = int(entry['TotalMerits'])
        merits_gained = int(entry['MeritsGained'])

        config.set('mc_power_name', power)
        config.set('mc_merit_total', total_merits)

        self.power_name.set(power)
        self.merit_total.set(str(total_merits))

        self.recalculate_current_power_rank()
        self.update_missing_merits()

        self.merit_session_int += merits_gained
        self.merit_session.set(str(self.merit_session_int))
        self.last_income.set(str(merits_gained))

    def handle_rank_event(self, entry: dict) -> None:
        rank = int(entry['Rank'])
        config.set('mc_power_rank', rank)
        self.power_rank.set(str(rank))
        self.update_missing_merits()
