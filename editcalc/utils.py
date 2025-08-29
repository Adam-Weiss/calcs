from __future__ import annotations
from typing import Any

def safe_float(v: Any, default: float = 0.0) -> float:
    try: return float(str(v).strip())
    except (ValueError, TypeError, AttributeError): return default

def safe_int(v: Any, default: int = 0) -> int:
    try: return int(str(v).strip())
    except (ValueError, TypeError, AttributeError): return default

def fmt_rate(rate: float) -> str:
    return f"{rate:.3f}"

def fmt_money_pair(amount_primary: float, cur_p: str, cur_s: str, rate: float) -> str:
    """Return '<curP><amtP>' or '<curP><amtP>  |  <curS><amtS> (@r)' if rate>0."""
    s_primary = f"{cur_p}{amount_primary:,.2f}"
    if rate > 0:
        return f"{s_primary}  |  {cur_s}{amount_primary*rate:,.2f} (@{fmt_rate(rate)})"
    return s_primary
