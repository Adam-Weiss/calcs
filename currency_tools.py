from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ui import PricingApp

def swap_currencies(app: "PricingApp") -> None:
    """Swap primary/secondary and invert rate (if > 0)."""
    p = app.var_cur_primary.get().strip()
    s = app.var_cur_secondary.get().strip()
    try:
        r = float(app.var_rate.get().strip())
    except Exception:
        r = 0.0

    if r > 0:
        app.var_cur_primary.set(s)
        app.var_cur_secondary.set(p)
        app.var_rate.set(f"{1.0 / r:.3f}")
        app.calculate()  # refresh
