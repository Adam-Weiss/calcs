from __future__ import annotations
from math import ceil
from typing import Optional
from .models import InputParams, CoreResults, SimulationTargets, SimulationResults

def compute_core(inp: InputParams) -> CoreResults:
    chars = inp.chars
    words = inp.words
    sheet_price = inp.sheet_price_primary
    sheet_size = inp.sheet_size_chars
    page_words = inp.standard_page_words
    rate = inp.exchange_rate

    avg = None
    wps = None
    if chars > 0 and words > 0:
        avg = chars / words
        if avg > 0 and sheet_size > 0:
            wps = sheet_size / avg

    p_char_p = p_word_p = p_page_p = None
    p_char_s = p_word_s = p_page_s = None
    sheets_exact = None
    sheets_rounded = None
    cost_exact_p = cost_rounded_p = None
    cost_exact_s = cost_rounded_s = None

    if sheet_price > 0 and sheet_size > 0:
        p_char_p = sheet_price / sheet_size
        if wps and wps > 0:
            p_word_p = sheet_price / wps
            if page_words > 0:
                p_page_p = p_word_p * page_words  # type: ignore

        if chars > 0:
            sheets_exact = chars / sheet_size
            sheets_rounded = ceil(sheets_exact)
            cost_exact_p = sheets_exact * sheet_price
            cost_rounded_p = sheets_rounded * sheet_price

        if rate > 0:
            if p_char_p is not None: p_char_s = p_char_p * rate
            if p_word_p is not None: p_word_s = p_word_p * rate
            if p_page_p is not None: p_page_s = p_page_p * rate
            if cost_exact_p is not None: cost_exact_s = cost_exact_p * rate
            if cost_rounded_p is not None: cost_rounded_s = cost_rounded_p * rate

    return CoreResults(
        avg_chars_per_word=avg,
        words_per_sheet=wps,
        price_per_char_primary=p_char_p,
        price_per_word_primary=p_word_p,
        price_per_page_primary=p_page_p,
        price_per_char_secondary=p_char_s,
        price_per_word_secondary=p_word_s,
        price_per_page_secondary=p_page_s,
        sheets_exact=sheets_exact,
        sheets_rounded=sheets_rounded,
        cost_exact_primary=cost_exact_p,
        cost_exact_secondary=cost_exact_s,
        cost_rounded_primary=cost_rounded_p,
        cost_rounded_secondary=cost_rounded_s,
    )

def simulate(inp: InputParams, core: CoreResults, targets: SimulationTargets) -> SimulationResults:
    sheet_price = inp.sheet_price_primary
    sheet_size = inp.sheet_size_chars
    rate = inp.exchange_rate

    def sheets_for_chars(nchars: Optional[float]) -> Optional[float]:
        if not nchars or nchars <= 0 or sheet_size <= 0: return None
        return nchars / sheet_size

    # derive chars from words/pages using avg
    avg = core.avg_chars_per_word or 0.0
    chars_from_words = (targets.target_words * avg) if (targets.target_words and avg > 0) else None
    chars_from_pages = ((targets.target_pages * inp.standard_page_words) * avg) if (targets.target_pages and avg > 0 and inp.standard_page_words > 0) else None

    # a) by chars
    s_c = sheets_for_chars(targets.target_chars)
    cost_c_p = (s_c * sheet_price) if (s_c and sheet_price > 0) else None
    cost_c_s = (cost_c_p * rate) if (cost_c_p and rate > 0) else None

    # b) by words
    s_w = sheets_for_chars(chars_from_words)
    cost_w_p = (s_w * sheet_price) if (s_w and sheet_price > 0) else None
    cost_w_s = (cost_w_p * rate) if (cost_w_p and rate > 0) else None

    # c) by pages
    s_p = sheets_for_chars(chars_from_pages)
    cost_p_p = (s_p * sheet_price) if (s_p and sheet_price > 0) else None
    cost_p_s = (cost_p_p * rate) if (cost_p_p and rate > 0) else None

    return SimulationResults(
        sim_sheets_by_chars=s_c,
        sim_cost_by_chars_primary=cost_c_p,
        sim_cost_by_chars_secondary=cost_c_s,
        sim_sheets_by_words=s_w,
        sim_cost_by_words_primary=cost_w_p,
        sim_cost_by_words_secondary=cost_w_s,
        sim_sheets_by_pages=s_p,
        sim_cost_by_pages_primary=cost_p_p,
        sim_cost_by_pages_secondary=cost_p_s,
    )
