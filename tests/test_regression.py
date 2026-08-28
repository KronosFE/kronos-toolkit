"""Frozen-anchor regression as a pytest suite.

    pytest tests/                 # or: python -m kronos_toolkit.verify.regression
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kronos_toolkit.verify.regression import run_regression


def test_all_frozen_anchors_pass():
    all_pass, results = run_regression(verbose=False)
    failed = [r["label"] for r in results if not r["ok"]]
    assert all_pass, f"anchor drift: {failed}"


def test_economics_firewall_blocks_public_leak():
    from kronos_toolkit.report.guard import assert_public_clean, EconomicsLeak
    import pytest
    with pytest.raises(EconomicsLeak):
        assert_public_clean({"note": "LCOE is $50/MWh"}, where="test")
    # clean payload passes
    assert assert_public_clean({"Q": 3.42, "note": "net TBR 0.74"})


def test_surrogates_are_tagged_T_and_name_their_retirer():
    from kronos_toolkit.hifi import ADAPTERS
    for name, ad in ADAPTERS.items():
        res = ad.run(force_surrogate=True)
        assert res.tag == "T", f"{name} not tagged [T]"
        assert res.retired_by, f"{name} surrogate does not name its retiring code"
