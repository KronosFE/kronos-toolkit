"""Blank study scaffold — copy this, fill in the four fields and your sweep.

Run:  python study_template/_template.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kronos_toolkit.report import Study
from kronos_toolkit.core import evaluate_breeder   # or solve_mirror, surplus_kg_per_fpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_results", "my_study")


def main(stamp=None):
    s = Study("my_study", out_dir=OUT, public=True, stamp=stamp)
    s.pre_register(
        question="WHAT decision does this study inform?",
        hypothesis="WHAT do you expect, stated before running?",
        method="WHICH engines + WHAT sweep?",
        gate="WHAT is the pass/fail line?",
        tags=[],
    )

    # Define your cases (one dict per configuration).
    cases = [
        dict(fuel="DT", R0=1.2, A=2.5, kappa=2.0, B0=B0, q95=3.0,
             fG=0.3, Ti0=15.0, TBR_dt=1.8, f_he4=0.05)
        for B0 in (6.0, 7.0, 8.0)
    ]
    s.run(evaluate_breeder, cases, columns=["Q", "P_fus_MW", "Ip_MA"])

    s.to_csv()
    s.manifest()
    s.verdict("CONDITIONAL", "state the honest result against the gate", evidence={})
    print(f"outputs -> {OUT}")
    return s


if __name__ == "__main__":
    main()
