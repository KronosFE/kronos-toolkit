"""Frozen-anchor regression suite.

Run as: python -m kronos_toolkit.verify.regression
All anchors must pass — proves the toolkit equals the frozen record.
"""
import sys
from .anchors import (
    BREEDER_DP, BREEDER_ANCHORS,
    BURNER_DP, BURNER_ANCHORS,
    SURPLUS_ANCHORS, NEUTRONICS_ANCHORS,
)


def _check(label, got, expected, atol):
    ok = abs(got - expected) <= atol
    status = "PASS" if ok else "FAIL"
    return dict(label=label, got=got, expected=expected, atol=atol, ok=ok, status=status)


def run_regression(verbose=True):
    """Run all frozen-anchor tests. Returns (all_pass, results_list)."""
    from ..core.breeder import evaluate_breeder
    from ..core.mirror_balance import solve_mirror
    from ..core.tritium import surplus_kg_per_fpy

    results = []

    # --- BREEDER ---
    br = evaluate_breeder(**BREEDER_DP)
    for name, anchor in BREEDER_ANCHORS.items():
        got = br[anchor["key"]]
        scale = anchor.get("scale", 1)
        results.append(_check(
            f"breeder.{name}", got * scale, anchor["value"], anchor["atol"]))

    # --- BURNER ---
    bu = solve_mirror(**BURNER_DP)
    for name, anchor in BURNER_ANCHORS.items():
        got = bu[anchor["key"]]
        scale = anchor.get("scale", 1)
        results.append(_check(
            f"burner.{name}", got * scale, anchor["value"], anchor["atol"]))

    # --- SURPLUS LAW ---
    for sa in SURPLUS_ANCHORS:
        got = surplus_kg_per_fpy(sa["net_tbr"])
        results.append(_check(
            f"surplus.{sa['net_tbr']:.2f}", got, sa["expected_kg"], sa["atol"]))

    # --- NEUTRONICS (analytic TBR surrogate at defaults) ---
    from ..neutronics import tbr
    nt = tbr().value
    for name, anchor in NEUTRONICS_ANCHORS.items():
        results.append(_check(
            f"neutronics.{name}", nt[anchor["key"]], anchor["value"], anchor["atol"]))

    # --- HIFI (each surrogate pinned to its frozen anchor) ---
    from ..hifi import ADAPTERS
    for name, ad in ADAPTERS.items():
        anc = ad.ANCHOR
        exp = anc.get("value")
        if exp is None:
            continue
        got = ad.run().value.get(anc["key"])
        results.append(_check(
            f"hifi.{name}", got, exp, anc.get("atol", 1e-9)))

    all_pass = all(r["ok"] for r in results)

    if verbose:
        hdr = f"{'Test':<25s} {'Expected':>12s} {'Got':>14s} {'Tol':>10s} {'Status':>6s}"
        print(hdr)
        print("-" * len(hdr))
        for r in results:
            print(f"{r['label']:<25s} {r['expected']:>12.6f} {r['got']:>14.6f} "
                  f"{r['atol']:>10.4f} {r['status']:>6s}")
        print()
        print(f"{'ALL PASS' if all_pass else 'FAILURES DETECTED'} "
              f"({sum(r['ok'] for r in results)}/{len(results)})")

    return all_pass, results


if __name__ == "__main__":
    ok, _ = run_regression(verbose=True)
    sys.exit(0 if ok else 1)
