from __future__ import annotations
from typing import Dict, Any, List
from .models import InputParams, CoreResults, SimulationTargets, SimulationResults

CSV_HEADERS: List[str] = [
    # inputs
    "characters","words","sheet_size_chars","standard_page_words",
    "sheet_price_primary","currency_primary","currency_secondary","exchange_rate_sec_per_prim",
    # core metrics
    "avg_chars_per_word","words_per_sheet",
    "price_per_char_primary","price_per_char_secondary",
    "price_per_word_primary","price_per_word_secondary",
    "price_per_page_primary","price_per_page_secondary",
    "sheets_exact","sheets_rounded",
    "cost_exact_primary","cost_exact_secondary",
    "cost_rounded_primary","cost_rounded_secondary",
    # simulation inputs
    "sim_target_chars","sim_target_words","sim_target_pages",
    # simulation outputs
    "sim_sheets_by_chars","sim_cost_by_chars_primary","sim_cost_by_chars_secondary",
    "sim_sheets_by_words","sim_cost_by_words_primary","sim_cost_by_words_secondary",
    "sim_sheets_by_pages","sim_cost_by_pages_primary","sim_cost_by_pages_secondary",
]

def build_row(inp: InputParams, core: CoreResults,
              sim_in: SimulationTargets, sim_out: SimulationResults) -> Dict[str, Any]:
    return {
        "characters": inp.chars,
        "words": inp.words,
        "sheet_size_chars": inp.sheet_size_chars,
        "standard_page_words": inp.standard_page_words,
        "sheet_price_primary": inp.sheet_price_primary,
        "currency_primary": inp.currency_primary,
        "currency_secondary": inp.currency_secondary,
        "exchange_rate_sec_per_prim": inp.exchange_rate if inp.exchange_rate > 0 else None,

        "avg_chars_per_word": core.avg_chars_per_word,
        "words_per_sheet": core.words_per_sheet,
        "price_per_char_primary": core.price_per_char_primary,
        "price_per_char_secondary": core.price_per_char_secondary,
        "price_per_word_primary": core.price_per_word_primary,
        "price_per_word_secondary": core.price_per_word_secondary,
        "price_per_page_primary": core.price_per_page_primary,
        "price_per_page_secondary": core.price_per_page_secondary,
        "sheets_exact": core.sheets_exact,
        "sheets_rounded": core.sheets_rounded,
        "cost_exact_primary": core.cost_exact_primary,
        "cost_exact_secondary": core.cost_exact_secondary,
        "cost_rounded_primary": core.cost_rounded_primary,
        "cost_rounded_secondary": core.cost_rounded_secondary,

        "sim_target_chars": sim_in.target_chars,
        "sim_target_words": sim_in.target_words,
        "sim_target_pages": sim_in.target_pages,
        "sim_sheets_by_chars": sim_out.sim_sheets_by_chars,
        "sim_cost_by_chars_primary": sim_out.sim_cost_by_chars_primary,
        "sim_cost_by_chars_secondary": sim_out.sim_cost_by_chars_secondary,
        "sim_sheets_by_words": sim_out.sim_sheets_by_words,
        "sim_cost_by_words_primary": sim_out.sim_cost_by_words_primary,
        "sim_cost_by_words_secondary": sim_out.sim_cost_by_words_secondary,
        "sim_sheets_by_pages": sim_out.sim_sheets_by_pages,
        "sim_cost_by_pages_primary": sim_out.sim_cost_by_pages_primary,
        "sim_cost_by_pages_secondary": sim_out.sim_cost_by_pages_secondary,
    }
