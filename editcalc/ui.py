from __future__ import annotations

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import IO, Optional, cast

from .models import InputParams, SimulationTargets
from . import engine, exporter
from .utils import safe_float, fmt_money_pair
from . import currency_tools

class PricingApp(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=12)
        self.winfo_toplevel().title("Word/Character Pricing Helper — Modular")
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Inputs
        self.var_chars = tk.StringVar()
        self.var_words = tk.StringVar()
        self.var_sheet_price = tk.StringVar()
        self.var_sheet_size = tk.StringVar(value="24000")
        self.var_page_words = tk.StringVar(value="250")
        self.var_cur_primary = tk.StringVar(value="$")
        self.var_cur_secondary = tk.StringVar(value="₪")
        self.var_rate = tk.StringVar()  # blank = primary only

        # Simulation
        self.var_sim_chars = tk.StringVar()
        self.var_sim_words = tk.StringVar()
        self.var_sim_pages = tk.StringVar()

        # Outputs (labels)
        self.out_avg_cpw = tk.StringVar(value="—")
        self.out_words_per_sheet = tk.StringVar(value="—")
        self.out_price_per_char = tk.StringVar(value="—")
        self.out_price_per_word = tk.StringVar(value="—")
        self.out_price_per_page = tk.StringVar(value="—")
        self.out_cost_exact = tk.StringVar(value="—")
        self.out_cost_rounded = tk.StringVar(value="—")

        self.out_sim_cost_chars = tk.StringVar(value="—")
        self.out_sim_cost_words = tk.StringVar(value="—")
        self.out_sim_cost_pages = tk.StringVar(value="—")

        self._build_ui()

    # ---------- UI building ----------
    def _build_ui(self) -> None:
        frm_in = ttk.LabelFrame(self, text="Inputs")
        frm_in.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        for i in range(6): frm_in.columnconfigure(i, weight=1)

        ttk.Label(frm_in, text="Characters (with spaces):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm_in, textvariable=self.var_chars).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm_in, text="Words:").grid(row=0, column=2, sticky="w")
        ttk.Entry(frm_in, textvariable=self.var_words).grid(row=0, column=3, sticky="ew")

        ttk.Label(frm_in, text="Price / printer’s sheet (primary):").grid(row=1, column=0, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, textvariable=self.var_sheet_price).grid(row=1, column=1, sticky="ew", pady=(4,0))

        ttk.Label(frm_in, text="Sheet size (chars):").grid(row=1, column=2, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, textvariable=self.var_sheet_size).grid(row=1, column=3, sticky="ew", pady=(4,0))

        ttk.Label(frm_in, text="Standard page (words):").grid(row=1, column=4, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, textvariable=self.var_page_words).grid(row=1, column=5, sticky="ew", pady=(4,0))

        ttk.Label(frm_in, text="Primary currency:").grid(row=2, column=0, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, width=6, textvariable=self.var_cur_primary).grid(row=2, column=1, sticky="w", pady=(4,0))

        ttk.Label(frm_in, text="Secondary currency:").grid(row=2, column=2, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, width=6, textvariable=self.var_cur_secondary).grid(row=2, column=3, sticky="w", pady=(4,0))

        ttk.Label(frm_in, text="Exchange rate (1 primary = ? secondary):").grid(row=2, column=4, sticky="w", pady=(4,0))
        ttk.Entry(frm_in, textvariable=self.var_rate).grid(row=2, column=5, sticky="ew", pady=(4,0))

        frm_btn = ttk.Frame(self)
        frm_btn.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        for i in range(5): frm_btn.columnconfigure(i, weight=1)

        ttk.Button(frm_btn, text="Calculate", command=self.calculate).grid(row=0, column=0, sticky="ew", padx=(0,4))
        ttk.Button(frm_btn, text="Reset", command=self.reset).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(frm_btn, text="Swap currencies", command=lambda: currency_tools.swap_currencies(self)).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(frm_btn, text="Copy CSV row", command=self.copy_csv_row).grid(row=0, column=3, sticky="ew", padx=4)
        ttk.Button(frm_btn, text="Export CSV…", command=self.export_csv).grid(row=0, column=4, sticky="ew", padx=(4,0))

        frm_out = ttk.LabelFrame(self, text="Results")
        frm_out.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        for i in range(2): frm_out.columnconfigure(i, weight=1)

        self._kv(frm_out, "Average chars/word:", self.out_avg_cpw, 0)
        self._kv(frm_out, "Words per sheet (≈):", self.out_words_per_sheet, 1)
        self._kv(frm_out, "Price per character:", self.out_price_per_char, 2)
        self._kv(frm_out, "Price per word:", self.out_price_per_word, 3)
        self._kv(frm_out, "Price per 250-word page:", self.out_price_per_page, 4)
        self._kv(frm_out, "Cost (exact, proportional):", self.out_cost_exact, 5)
        self._kv(frm_out, "Cost (rounded up sheets):", self.out_cost_rounded, 6)

        frm_sim = ttk.LabelFrame(self, text="Simulate different lengths (keeps avg chars/word)")
        frm_sim.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        for i in range(4): frm_sim.columnconfigure(i, weight=1)

        ttk.Label(frm_sim, text="Target characters:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm_sim, textvariable=self.var_sim_chars).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm_sim, text="Target words:").grid(row=0, column=2, sticky="w")
        ttk.Entry(frm_sim, textvariable=self.var_sim_words).grid(row=0, column=3, sticky="ew")

        ttk.Label(frm_sim, text="Target standard pages:").grid(row=1, column=0, sticky="w", pady=(4,0))
        ttk.Entry(frm_sim, textvariable=self.var_sim_pages).grid(row=1, column=1, sticky="ew", pady=(4,0))

        ttk.Button(frm_sim, text="Run Simulation", command=self.simulate).grid(row=1, column=3, sticky="e", pady=(4,0))

        frm_sim_out = ttk.LabelFrame(self, text="Simulation results")
        frm_sim_out.grid(row=4, column=0, sticky="ew", padx=4, pady=4)
        for i in range(2): frm_sim_out.columnconfigure(i, weight=1)

        self._kv(frm_sim_out, "Sim cost (by target chars):", self.out_sim_cost_chars, 0)
        self._kv(frm_sim_out, "Sim cost (by target words):", self.out_sim_cost_words, 1)
        self._kv(frm_sim_out, "Sim cost (by target pages):", self.out_sim_cost_pages, 2)

    @staticmethod
    def _kv(parent: ttk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="e", pady=2)

    # ---------- Wiring to engine ----------
    def _read_inputs(self) -> InputParams:
        return InputParams(
            chars=safe_float(self.var_chars.get()),
            words=safe_float(self.var_words.get()),
            sheet_price_primary=safe_float(self.var_sheet_price.get()),
            sheet_size_chars=safe_float(self.var_sheet_size.get(), 24000.0),
            standard_page_words=safe_float(self.var_page_words.get(), 250.0),
            currency_primary=(self.var_cur_primary.get() or "$").strip(),
            currency_secondary=(self.var_cur_secondary.get() or "₪").strip(),
            exchange_rate=safe_float(self.var_rate.get()),
        )

    def calculate(self) -> None:
        inp = self._read_inputs()
        core = engine.compute_core(inp)

        self.out_avg_cpw.set("—" if core.avg_chars_per_word is None else f"{core.avg_chars_per_word:,.3f}")
        self.out_words_per_sheet.set("—" if core.words_per_sheet is None else f"{core.words_per_sheet:,.1f}")

        cur_p, cur_s, rate = inp.currency_primary, inp.currency_secondary, inp.exchange_rate

        def set_money_or_dash(var: tk.StringVar, primary_amount: Optional[float]) -> None:
            var.set("—" if primary_amount is None else fmt_money_pair(primary_amount, cur_p, cur_s, rate))

        set_money_or_dash(self.out_price_per_char, core.price_per_char_primary)
        set_money_or_dash(self.out_price_per_word, core.price_per_word_primary)
        set_money_or_dash(self.out_price_per_page, core.price_per_page_primary)

        if core.cost_exact_primary is not None and core.sheets_exact is not None:
            self.out_cost_exact.set(f"{fmt_money_pair(core.cost_exact_primary, cur_p, cur_s, rate)}  ({core.sheets_exact:,.3f} sheets)")
        else:
            self.out_cost_exact.set("—")

        if core.cost_rounded_primary is not None and core.sheets_rounded is not None:
            self.out_cost_rounded.set(f"{fmt_money_pair(core.cost_rounded_primary, cur_p, cur_s, rate)}  ({core.sheets_rounded} sheets)")
        else:
            self.out_cost_rounded.set("—")

        # cache latest core for simulation/export
        self._last_inp = inp
        self._last_core = core

    def _ensure_core(self) -> bool:
        if not hasattr(self, "_last_core"):
            self.calculate()
        return hasattr(self, "_last_core")

    def simulate(self) -> None:
        if not self._ensure_core():
            messagebox.showwarning("Missing data", "Calculate first (need average chars/word).")
            return

        inp = self._last_inp  # type: ignore[attr-defined]
        core = self._last_core  # type: ignore[attr-defined]
        targets = SimulationTargets(
            target_chars=safe_float(self.var_sim_chars.get()),
            target_words=safe_float(self.var_sim_words.get()),
            target_pages=safe_float(self.var_sim_pages.get()),
        )
        sim = engine.simulate(inp, core, targets)

        cur_p, cur_s, rate = inp.currency_primary, inp.currency_secondary, inp.exchange_rate

        def label_from(cost_p: Optional[float], sheets: Optional[float]) -> str:
            if sheets is None: return "—"
            if cost_p is None: return f"≈ {sheets:,.3f} sheets"
            return f"{fmt_money_pair(cost_p, cur_p, cur_s, rate)}  ({sheets:,.3f} sheets)"

        self.out_sim_cost_chars.set(label_from(sim.sim_cost_by_chars_primary, sim.sim_sheets_by_chars))
        self.out_sim_cost_words.set(label_from(sim.sim_cost_by_words_primary, sim.sim_sheets_by_words))
        self.out_sim_cost_pages.set(label_from(sim.sim_cost_by_pages_primary, sim.sim_sheets_by_pages))

        self._last_sim_in = targets
        self._last_sim_out = sim

    # ---------- Export / Copy ----------
    def _gather_for_export(self):
        if not hasattr(self, "_last_core"):
            self.calculate()
        if not hasattr(self, "_last_sim_out"):
            # build empty sim if none yet
            self._last_sim_in = SimulationTargets(None, None, None)
            self._last_sim_out = engine.simulate(self._last_inp, self._last_core, self._last_sim_in)  # type: ignore
        return self._last_inp, self._last_core, self._last_sim_in, self._last_sim_out  # type: ignore

    def export_csv(self) -> None:
        inp, core, sim_in, sim_out = self._gather_for_export()
        row = exporter.build_row(inp, core, sim_in, sim_out)
        path = filedialog.asksaveasfilename(
            title="Export results to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(cast(IO[str], f), fieldnames=exporter.CSV_HEADERS)
                writer.writeheader()
                writer.writerow(row)
            messagebox.showinfo("Exported", f"Results exported to:\n{path}")
        except OSError as e:
            messagebox.showerror("Export failed", f"Could not write CSV:\n{e}")

    def copy_csv_row(self) -> None:
        inp, core, sim_in, sim_out = self._gather_for_export()
        row = exporter.build_row(inp, core, sim_in, sim_out)
        values = [(row.get(h) if row.get(h) is not None else "") for h in exporter.CSV_HEADERS]
        csv_line = ",".join(str(v) for v in values)
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(csv_line)
            self.master.update_idletasks()
            messagebox.showinfo("Copied", "CSV row copied to clipboard.")
        except tk.TclError as e:
            messagebox.showerror("Copy failed", f"Could not copy to clipboard:\n{e}")

    # ---------- Reset ----------
    def reset(self) -> None:
        for v in (self.var_chars, self.var_words, self.var_sheet_price,
                  self.var_sim_chars, self.var_sim_words, self.var_sim_pages,
                  self.var_rate):
            v.set("")
        self.var_sheet_size.set("24000")
        self.var_page_words.set("250")
        self.var_cur_primary.set("$")
        self.var_cur_secondary.set("₪")

        for v in (self.out_avg_cpw, self.out_words_per_sheet, self.out_price_per_char,
                  self.out_price_per_word, self.out_price_per_page,
                  self.out_cost_exact, self.out_cost_rounded,
                  self.out_sim_cost_chars, self.out_sim_cost_words, self.out_sim_cost_pages):
            v.set("—")
