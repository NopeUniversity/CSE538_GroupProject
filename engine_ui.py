# engine_ui.py
#
# Tkinter UI for the Game Engine analysis project.
# Uses parsing logic and Game class from GroupProject_Main.py

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Dict, List, Tuple, Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


from GroupProject_Main import fileRead, htmlToList, Game, compare_engines


# ---------- Data helpers ----------

def build_engine_dict(engine_list: List[list]) -> Dict[str, List[Game]]:
    """
    Convert engineList:
        [ [engine_name, Game, Game, ...], [engine_name2, Game, ...], ... ]
    into:
        { "Engine Name": [Game, Game, ...], ... }
    """
    engine_dict: Dict[str, List[Game]] = {}
    for entry in engine_list:
        if not entry:
            continue
        engine_name = entry[0]  # engine name is the first item
        games = entry[1:]       # the following items are game objects
        engine_dict[engine_name] = games
    return engine_dict


def _safe_avg(values: List[float]) -> float | None:
    usable = [v for v in values if v is not None and v >= 0]
    if not usable:
        return None
    return sum(usable) / len(usable)


def _safe_max(values: List[float]) -> float | None:
    usable = [v for v in values if v is not None and v >= 0]
    if not usable:
        return None
    return max(usable)


def compute_engine_stats(engine_name: str, games: List[Game]) -> Dict[str, Any]:
    """
    Compute averages and max values for one engine, including revenue estimates.
    Revenue per game = cost * topPlayerCount (only when both are valid >= 0).
    """
    costs = [g.cost for g in games]
    ratings = [g.rating for g in games]
    players = [g.topPlayerCount for g in games]

    revenues: List[float] = []
    for g in games:
        if g.cost is not None and g.cost >= 0 and \
           g.topPlayerCount is not None and g.topPlayerCount >= 0:
            revenues.append(g.cost * g.topPlayerCount)

    return {
        "engine_name": engine_name,
        "num_games": len(games),
        "avg_cost": _safe_avg(costs),
        "max_cost": _safe_max(costs),
        "avg_rating": _safe_avg(ratings),
        "max_rating": _safe_max(ratings),
        "avg_players": _safe_avg(players),
        "max_players": _safe_max(players),
        "avg_revenue": _safe_avg(revenues),
        "max_revenue": _safe_max(revenues),
    }


def _fmt(v: float | None, money: bool = False) -> str:
    if v is None or v < 0:
        return "N/A"
    if money:
        return f"${v:,.2f}"
    return f"{v:,.2f}"


# ---------- Plotting helpers ----------

def plot_bar_comparison(stats_list: List[Dict[str, Any]], metric_key: str) -> None:
    """
    metric_key is like "avg_cost", "max_rating", "avg_players", "max_players".
    (Revenue isn't wired into the bar chart yet.)
    """
    if not stats_list:
        messagebox.showinfo("Bar Chart", "No data to plot.")
        return

    prefix, _, base = metric_key.partition("_")  # "avg", "_", "cost"
    base_labels = {
        "cost": "Price ($)",
        "rating": "Rating",
        "players": "Peak Players",
    }
    stat_prefix = "Average" if prefix == "avg" else "Max"
    y_label = f"{stat_prefix} {base_labels.get(base, base)}"

    names = [s["engine_name"] for s in stats_list]
    values: List[float] = []
    for s in stats_list:
        v = s.get(metric_key)
        if v is None or v < 0:
            values.append(0.0)
        else:
            values.append(float(v))

    x_positions = range(len(names))

    plt.figure()
    plt.bar(x_positions, values)
    plt.xticks(list(x_positions), names, rotation=45, ha="right")
    plt.ylabel(y_label)
    plt.title(f"{y_label} by Engine")
    plt.tight_layout()
    plt.show()


def plot_line_for_engine(engine_name: str, games: List[Game]) -> None:
    """
    Line chart for a single engine.

    X-axis: release date (time)
    Y-axis: peak players per game

    Includes games that have:
        - a valid datetime releaseDate
        - topPlayerCount > 0
    """
    if not games:
        messagebox.showinfo("Line Chart", "No games to plot.")
        return

    points: List[Tuple[datetime, float, str]] = []

    for g in games:
        rd = getattr(g, "releaseDate", None)
        if not isinstance(rd, datetime):
            continue
        if g.topPlayerCount is None or g.topPlayerCount <= 0:
            continue

        title_clean = g.title.lstrip(">").strip()
        points.append((rd, g.topPlayerCount, title_clean))

    if not points:
        messagebox.showinfo(
            "Line Chart",
            "No games with valid release date and peak players > 0."
        )
        return

    # sort by release date (oldest -> newest)
    points.sort(key=lambda p: p[0])

    dates = [p[0] for p in points]
    peaks = [p[1] for p in points]
    labels = [p[2] for p in points]

    fig, ax = plt.subplots()
    ax.plot(dates, peaks, marker="o")

    # format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=45, ha="right")

    ax.set_ylabel("Peak Players")
    ax.set_title(f"Peak Players Over Time – {engine_name}")

    # Optional: label each point with the game title
    for d, p, label in zip(dates, peaks, labels):
        ax.annotate(
            label,
            (d, p),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=8,
        )

    plt.tight_layout()
    plt.show()




# ---------- Tkinter App ----------

# noinspection PyTypeChecker
class EngineApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Game Engine Analysis UI")
        self.geometry("1000x640")

        self.engine_dict: Dict[str, List[Game]] = {}
        self.engine_names: List[str] = []

        # Active filters (None = no filter)
        # rating_filter: (min_rating, max_rating)
        # release_filter: (start_year, end_year)
        # price_filter: (min_price, max_price or None)
        self.rating_filter: Tuple[float, float] | None = None
        self.release_filter: Tuple[int | None, int | None] | None = None
        self.price_filter: Tuple[float, float | None] | None = None

        self._build_widgets()

    # --- UI layout ---

    def _build_widgets(self):
        # Top frame: folder controls
        top = ttk.Frame(self)
        top.pack(side=tk.TOP,
                 fill=tk.X,
                 padx=8,
                 pady=4)

        ttk.Label(top, text="Data folder:").pack(side=tk.LEFT)
        self.folder_label = ttk.Label(top, text="(none loaded)")
        self.folder_label.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        ttk.Button(top, text="Load Folder...", command=self.load_folder).pack(side=tk.RIGHT, padx=4)

        # Middle frame: two listboxes (all engines, selected engines)
        mid = ttk.Frame(self)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: all engines
        left_frame = ttk.Frame(mid)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="All Engines").pack(anchor="w")
        self.list_all = tk.Listbox(left_frame, selectmode=tk.EXTENDED)
        self.list_all.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_all = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.list_all.yview)
        scrollbar_all.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_all.config(yscrollcommand=scrollbar_all.set)

        # Center: buttons to move between lists
        center_frame = ttk.Frame(mid)
        center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(center_frame, text="Add ->", command=self.add_selected).pack(pady=4)
        ttk.Button(center_frame, text="<- Remove", command=self.remove_selected).pack(pady=4)
        ttk.Button(center_frame, text="Clear Selected", command=self.clear_selected).pack(pady=4)

        # Right: selected engines
        right_frame = ttk.Frame(mid)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Selected Engines (for comparison / charts)").pack(anchor="w")
        self.list_selected = tk.Listbox(right_frame, selectmode=tk.EXTENDED)
        self.list_selected.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_sel = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.list_selected.yview)
        scrollbar_sel.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_selected.config(yscrollcommand=scrollbar_sel.set)

        # Bottom frame: actions + log
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=8, pady=4)

        button_frame = ttk.Frame(bottom)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(button_frame, text="Stats for one engine", command=self.ui_show_stats).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Filter by rating range", command=self.ui_rating_filter).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Filter by release year", command=self.ui_release_filter).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Filter by price", command=self.ui_price_filter).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Clear filters", command=self.ui_clear_filters).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Compare selected (text)", command=self.ui_compare_selected).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Bar chart (selected)", command=self.ui_bar_chart).pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(button_frame, text="Line chart (selected one)", command=self.ui_line_chart).pack(side=tk.LEFT, padx=4, pady=2)

        # Log output
        ttk.Label(bottom, text="Output:").pack(anchor="w")
        self.output_text = tk.Text(bottom, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    # --- Data loading ---

    def load_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing engine HTML files")
        if not folder:
            return

        try:
            engine_file_list = fileRead(folder)
            engine_list = htmlToList(engine_file_list)
            engine_dict = build_engine_dict(engine_list)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data:\n{e}")
            return

        if not engine_dict:
            messagebox.showwarning("No Data", "No engines found in that folder.")
            return

        self.engine_dict = engine_dict
        self.engine_names = sorted(engine_dict.keys())

        # reset filters when loading a new folder
        self.rating_filter = None
        self.release_filter = None
        self.price_filter = None

        self.folder_label.config(text=folder)
        self._refresh_all_listbox()

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Loaded {len(self.engine_names)} engines.\n")
        for name in self.engine_names[:10]:
            self.output_text.insert(tk.END, f"  - {name}\n")
        if len(self.engine_names) > 10:
            self.output_text.insert(tk.END, "  ...\n")

    def _refresh_all_listbox(self):
        self.list_all.delete(0, tk.END)
        for name in self.engine_names:
            self.list_all.insert(tk.END, name)

    # --- listbox manipulation ---

    def add_selected(self):
        for idx in self.list_all.curselection():
            name = self.list_all.get(idx)
            if name not in self.list_selected.get(0, tk.END):
                self.list_selected.insert(tk.END, name)

    def remove_selected(self):
        selection = list(self.list_selected.curselection())
        selection.reverse()
        for idx in selection:
            self.list_selected.delete(idx)

    def clear_selected(self):
        self.list_selected.delete(0, tk.END)

    # --- Filter core logic ---

    def _get_filtered_games(self) -> List[Tuple[str, Game]]:
        """
        Apply all active filters (rating, release year, price) and
        return a list of (engine_name, Game) that satisfy ALL of them.
        """
        results: List[Tuple[str, Game]] = []

        for engine_name, games in self.engine_dict.items():
            for g in games:
                # Rating filter
                if self.rating_filter is not None:
                    min_r, max_r = self.rating_filter
                    if g.rating < 0 or g.rating < min_r or g.rating > max_r:
                        continue

                # Price filter
                if self.price_filter is not None:
                    min_p, max_p = self.price_filter
                    price = g.cost
                    if price is None or price < 0:
                        continue
                    if price < min_p:
                        continue
                    if max_p is not None and price > max_p:
                        continue

                # Release year filter
                if self.release_filter is not None:
                    start_year, end_year = self.release_filter
                    rd = getattr(g, "releaseDate", None)
                    if not isinstance(rd, datetime):
                        continue
                    year = rd.year
                    if start_year is not None and year < start_year:
                        continue
                    if end_year is not None and year > end_year:
                        continue

                results.append((engine_name, g))

        # Sort by engine then title
        results.sort(key=lambda tup: (tup[0], tup[1].title))
        return results

    def _render_filtered_results(self):
        """
        Print the current filter settings + the filtered game list into the output box.
        """
        self.output_text.delete("1.0", tk.END)

        # Build filter summary
        parts = []
        if self.rating_filter is not None:
            rmin, rmax = self.rating_filter
            parts.append(f"rating {rmin}–{rmax}")
        if self.release_filter is not None:
            sy, ey = self.release_filter
            s_str = str(sy) if sy is not None else "-∞"
            e_str = str(ey) if ey is not None else "+∞"
            parts.append(f"release years {s_str}–{e_str}")
        if self.price_filter is not None:
            pmin, pmax = self.price_filter
            pmax_str = f"{pmax:.2f}" if pmax is not None else "∞"
            parts.append(f"price {pmin:.2f}–{pmax_str}")

        if not parts:
            self.output_text.insert(tk.END, "No active filters. Set a rating, release year, or price filter.\n")
            return

        self.output_text.insert(tk.END, "Active filters: " + ", ".join(parts) + "\n")
        self.output_text.insert(tk.END, "-" * 80 + "\n")

        results = self._get_filtered_games()
        if not results:
            self.output_text.insert(tk.END, "No games found matching the current filter combination.\n")
            return

        for engine_name, g in results:
            rd = getattr(g, "releaseDate", None)
            date_str = rd.strftime("%Y-%m-%d") if isinstance(rd, datetime) else "Unknown"
            price_str = f"${g.cost:.2f}" if g.cost is not None and g.cost >= 0 else "N/A"
            rating_str = f"{g.rating:.2f}" if g.rating >= 0 else "N/A"
            line = (
                f"[{engine_name}] {g.title.lstrip('>').strip()} "
                f"(ID {g.id}) – rating {rating_str}, price {price_str}, release {date_str}\n"
            )
            self.output_text.insert(tk.END, line)

    # --- UI actions ---

    def ui_show_stats(self):
        name = self._get_single_engine_from_any_list()
        if not name:
            return

        games = self.engine_dict.get(name, [])
        stats = compute_engine_stats(name, games)

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"Engine: {stats['engine_name']}\n")
        self.output_text.insert(tk.END, f"Games counted: {stats['num_games']}\n\n")
        self.output_text.insert(tk.END, f"Avg price:        {_fmt(stats['avg_cost'], money=True)}\n")
        self.output_text.insert(tk.END, f"Max price:        {_fmt(stats['max_cost'], money=True)}\n\n")
        self.output_text.insert(tk.END, f"Avg rating:       {_fmt(stats['avg_rating'])}\n")
        self.output_text.insert(tk.END, f"Max rating:       {_fmt(stats['max_rating'])}\n\n")
        self.output_text.insert(tk.END, f"Avg peak players: {_fmt(stats['avg_players'])}\n")
        self.output_text.insert(tk.END, f"Max peak players: {_fmt(stats['max_players'])}\n\n")
        self.output_text.insert(tk.END, f"Avg est. revenue: {_fmt(stats['avg_revenue'], money=True)}\n")
        self.output_text.insert(tk.END, f"Max est. revenue: {_fmt(stats['max_revenue'], money=True)}\n")

    def ui_rating_filter(self):
        if not self.engine_dict:
            messagebox.showinfo("Rating Filter", "Load a folder first.")
            return

        min_str = simpledialog.askstring("Rating Filter", "Minimum rating (0–100):")
        if min_str is None:
            return
        max_str = simpledialog.askstring("Rating Filter", "Maximum rating (0–100):")
        if max_str is None:
            return

        try:
            min_r = float(min_str)
            max_r = float(max_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid numbers.")
            return

        if min_r > max_r:
            min_r, max_r = max_r, min_r

        self.rating_filter = (min_r, max_r)
        self._render_filtered_results()

    def ui_release_filter(self):
        """
        Filter games by release year range (inclusive).
        Uses Game.releaseDate if it is a datetime; skips 'Unreleased'.
        """
        if not self.engine_dict:
            messagebox.showinfo("Release Filter", "Load a folder first.")
            return

        start_str = simpledialog.askstring(
            "Release Filter",
            "Start year (YYYY, blank for earliest):"
        )
        if start_str is None:
            return
        end_str = simpledialog.askstring(
            "Release Filter",
            "End year (YYYY, blank for latest):"
        )
        if end_str is None:
            return

        try:
            start_year = int(start_str) if start_str.strip() else None
            end_year = int(end_str) if end_str.strip() else None
        except ValueError:
            messagebox.showerror("Error", "Years must be integers like 2010.")
            return

        self.release_filter = (start_year, end_year)
        self._render_filtered_results()

    def ui_price_filter(self):
        """
        Filter games by price range in dollars.
        Uses Game.cost; skips negative or missing prices.
        """
        if not self.engine_dict:
            messagebox.showinfo("Price Filter", "Load a folder first.")
            return

        min_str = simpledialog.askstring("Price Filter", "Minimum price (e.g. 0 or 9.99):")
        if min_str is None:
            return
        max_str = simpledialog.askstring("Price Filter", "Maximum price (blank for no max):")
        if max_str is None:
            return

        try:
            min_p = float(min_str) if min_str.strip() else 0.0
            max_p = float(max_str) if max_str.strip() else None
        except ValueError:
            messagebox.showerror("Error", "Prices must be numbers like 14.99.")
            return

        self.price_filter = (min_p, max_p)
        self._render_filtered_results()

    def ui_clear_filters(self):
        """Reset all active filters and clear the filtered output."""
        self.rating_filter = None
        self.release_filter = None
        self.price_filter = None
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "All filters cleared.\n")

    def ui_compare_selected(self):
        selected_names = list(self.list_selected.get(0, tk.END))
        if not selected_names:
            messagebox.showinfo("Compare", "Pick engines in the Selected list first.")
            return
        if len(selected_names) > 5:
            selected_names = selected_names[:5]
            messagebox.showinfo("Compare", "Using first 5 selected engines.")

        stats_list = compare_engines(self.engine_dict, selected_names)
        if not stats_list:
            messagebox.showinfo("Compare", "None of the selected engines were found.")
            return

        # --- Ask: averages or max? ---
        mode_win = tk.Toplevel(self)
        mode_win.title("Choose stat type")

        mode_var = tk.StringVar(value="avg")

        ttk.Radiobutton(
            mode_win, text="Averages", value="avg", variable=mode_var
        ).pack(anchor="w", padx=8, pady=2)
        ttk.Radiobutton(
            mode_win, text="Max / Top values", value="max", variable=mode_var
        ).pack(anchor="w", padx=8, pady=2)

        def on_ok():
            mode = mode_var.get()  # "avg" or "max"
            mode_win.destroy()

            # Enrich stats_list with revenue stats per engine
            for s in stats_list:
                eng_name = s["engine_name"]
                games = self.engine_dict.get(eng_name, [])
                rev_stats = compute_engine_stats(eng_name, games)
                s["avg_revenue"] = rev_stats.get("avg_revenue")
                s["max_revenue"] = rev_stats.get("max_revenue")

            use_avg = (mode == "avg")
            label_prefix = "Average" if use_avg else "Max"

            cost_key = "avg_cost" if use_avg else "max_cost"
            rating_key = "avg_rating" if use_avg else "max_rating"
            players_key = "avg_players" if use_avg else "max_players"
            revenue_key = "avg_revenue" if use_avg else "max_revenue"

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END, f"Engine comparison ({label_prefix.lower()} values):\n"
            )
            self.output_text.insert(tk.END, "-" * 95 + "\n")
            header = (
                f"{'Engine':25s} "
                f"{'Games':>6s} "
                f"{label_prefix + ' $':>10s} "
                f"{label_prefix + ' Rating':>12s} "
                f"{label_prefix + ' Players':>14s} "
                f"{label_prefix + ' Revenue':>18s}\n"
            )
            self.output_text.insert(tk.END, header)
            self.output_text.insert(tk.END, "-" * 95 + "\n")

            for s in stats_list:
                line = (
                    f"{s['engine_name'][:25]:25s} "
                    f"{s['num_games']:>6d} "
                    f"{_fmt(s[cost_key], money=True):>10s} "
                    f"{_fmt(s[rating_key]):>12s} "
                    f"{_fmt(s[players_key]):>14s} "
                    f"{_fmt(s[revenue_key], money=True):>18s}\n"
                )
                self.output_text.insert(tk.END, line)

        ttk.Button(mode_win, text="OK", command=on_ok).pack(pady=8)

    def ui_bar_chart(self):
        selected_names = list(self.list_selected.get(0, tk.END))
        if not selected_names:
            messagebox.showinfo("Bar Chart", "Pick engines in the Selected list first.")
            return
        if len(selected_names) > 5:
            selected_names = selected_names[:5]
            messagebox.showinfo("Bar Chart", "Using first 5 selected engines.")

        stats_list = compare_engines(self.engine_dict, selected_names)
        if not stats_list:
            messagebox.showinfo("Bar Chart", "No valid engines to compare.")
            return

        metric_win = tk.Toplevel(self)
        metric_win.title("Choose metric")

        metric_var = tk.StringVar(value="cost")   # base metric
        mode_var = tk.StringVar(value="avg")      # "avg" or "max"

        ttk.Label(metric_win, text="Metric:").pack(anchor="w", padx=8, pady=(8, 2))
        ttk.Radiobutton(metric_win, text="Price", value="cost", variable=metric_var).pack(anchor="w", padx=16, pady=2)
        ttk.Radiobutton(metric_win, text="Rating", value="rating", variable=metric_var).pack(anchor="w", padx=16, pady=2)
        ttk.Radiobutton(metric_win, text="Peak players", value="players", variable=metric_var).pack(anchor="w", padx=16, pady=2)

        ttk.Label(metric_win, text="Stat type:").pack(anchor="w", padx=8, pady=(8, 2))
        ttk.Radiobutton(metric_win, text="Averages", value="avg", variable=mode_var).pack(anchor="w", padx=16, pady=2)
        ttk.Radiobutton(metric_win, text="Max / Top values", value="max", variable=mode_var).pack(anchor="w", padx=16, pady=2)

        def on_ok():
            base = metric_var.get()   # "cost"/"rating"/"players"
            mode = mode_var.get()     # "avg"/"max"
            metric_key = f"{mode}_{base}"   # e.g. "avg_cost" or "max_players"
            metric_win.destroy()
            plot_bar_comparison(stats_list, metric_key)

        ttk.Button(metric_win, text="OK", command=on_ok).pack(pady=8)

    def ui_line_chart(self):
        """
        Plot a line chart for a single engine:
        X-axis = release date, Y-axis = peak players per game.
        """
        name = self._get_single_engine_from_any_list()
        if not name:
            return

        games = self.engine_dict.get(name, [])
        if not games:
            messagebox.showinfo("Line Chart", f"No games found for engine '{name}'.")
            return

        plot_line_for_engine(name, games)

    # --- helper to pick a single engine ---

    def _get_single_engine_from_any_list(self) -> str | None:
        """
        Helper: get one engine either from selection in 'Selected' list,
        or (if none) from 'All Engines' list.
        """
        sel = self.list_selected.curselection()
        if sel:
            return self.list_selected.get(sel[0])

        sel_all = self.list_all.curselection()
        if sel_all:
            return self.list_all.get(sel_all[0])

        messagebox.showinfo("Select engine", "Click an engine in either list first.")
        return None


def main():
    app = EngineApp()
    app.mainloop()


if __name__ == "__main__":
    main()
