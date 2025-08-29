from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class InputParams:
    chars: float
    words: float
    sheet_price_primary: float     # in primary currency
    sheet_size_chars: float        # default 24000
    standard_page_words: float     # default 250
    currency_primary: str          # e.g. "$"
    currency_secondary: str        # e.g. "₪"
    # 1 primary = rate secondary; if <= 0, show only primary
    exchange_rate: float

@dataclass
class CoreResults:
    avg_chars_per_word: Optional[float]
    words_per_sheet: Optional[float]
    price_per_char_primary: Optional[float]
    price_per_word_primary: Optional[float]
    price_per_page_primary: Optional[float]
    price_per_char_secondary: Optional[float]
    price_per_word_secondary: Optional[float]
    price_per_page_secondary: Optional[float]
    sheets_exact: Optional[float]
    sheets_rounded: Optional[int]
    cost_exact_primary: Optional[float]
    cost_exact_secondary: Optional[float]
    cost_rounded_primary: Optional[float]
    cost_rounded_secondary: Optional[float]

@dataclass
class SimulationTargets:
    target_chars: Optional[float]
    target_words: Optional[float]
    target_pages: Optional[float]

@dataclass
class SimulationResults:
    # By chars
    sim_sheets_by_chars: Optional[float]
    sim_cost_by_chars_primary: Optional[float]
    sim_cost_by_chars_secondary: Optional[float]
    # By words
    sim_sheets_by_words: Optional[float]
    sim_cost_by_words_primary: Optional[float]
    sim_cost_by_words_secondary: Optional[float]
    # By pages
    sim_sheets_by_pages: Optional[float]
    sim_cost_by_pages_primary: Optional[float]
    sim_cost_by_pages_secondary: Optional[float]
