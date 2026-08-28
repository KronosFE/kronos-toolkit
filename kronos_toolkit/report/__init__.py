"""kronos_toolkit.report — study scaffold, brand plotting, table export, firewall.

    from kronos_toolkit.report import Study
    s = Study("my_scan", out_dir="results", public=True)
    s.pre_register(question=..., hypothesis=..., method=..., gate=...)
    s.run(evaluate_breeder, cases, columns=["Q", "P_fus_MW"])
    s.to_csv(); s.manifest(); s.verdict("NO-GO", "net power not reached")
"""
from .study import Study
from .guard import guard, assert_public_clean, scan, EconomicsLeak
from . import tables
from . import plotting
