"""Worked example 2 — coil buildability + hardening (stress-managed HTS).

Retrofit of the BC-B / BC-B2 coil-stress logic into the toolkit. Exercises:
hifi (struct_fea surrogate, the ~0.785x peak-fiber factor) + report scaffold.
The surrogate is the 0.785x side of the 0.26x/0.785x contradiction that real
FEA must adjudicate — flagged honestly as [T], retired_by ANSYS/COMSOL/Elmer.

Run:  python study_template/coil_buildability.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kronos_toolkit.hifi import ADAPTERS
from kronos_toolkit.report import Study

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_results", "coil_buildability")

# REBCO allowable (Von Mises) working stress band [MPa] — literature scoping.
REBCO_ALLOWABLE_MPA = 660.0

B_FIELD_LADDER = [12.0, 14.0, 17.0, 20.0, 23.0]     # on-coil field [T]


def build_rows():
    fea = ADAPTERS["struct_fea"]
    rows = []
    for B in B_FIELD_LADDER:
        res = fea.run(B_T=B, r_bore_m=0.20, r_out_m=0.40).value
        peak = res["peak_fiber_stress_MPa"]
        rows.append(dict(
            B_T=B,
            magnetic_pressure_MPa=res["magnetic_pressure_MPa"],
            peak_fiber_stress_MPa=peak,
            peak_fiber_factor=res["peak_fiber_factor"],
            buildable=("yes" if peak <= REBCO_ALLOWABLE_MPA else "no"),
        ))
    return rows


def main(stamp=None):
    study = Study("coil_buildability", out_dir=OUT, public=True, stamp=stamp)
    study.pre_register(
        question="Up to what on-coil field is the HTS plug coil buildable within REBCO allowables?",
        hypothesis="Peak-fiber stress crosses the REBCO allowable between 17 and 23 T.",
        method="thick-wall Lame peak-fiber surrogate (hifi.struct_fea) over a field ladder.",
        gate=f"buildable = peak-fiber stress <= {REBCO_ALLOWABLE_MPA} MPa (REBCO allowable)",
        tags=["burner", "coil", "structural"],
    )

    rows = build_rows()
    study.add_rows(rows, columns=["B_T", "magnetic_pressure_MPa",
                                  "peak_fiber_stress_MPa", "peak_fiber_factor",
                                  "buildable"])
    study.to_csv()
    study.manifest(anchors={"peak_fiber_factor": {"value": 0.785, "atol": 1e-9}})

    buildable = [r["B_T"] for r in rows if r["buildable"] == "yes"]
    max_field = max(buildable) if buildable else None
    v = study.verdict(
        "CONDITIONAL",
        rationale=(f"Buildable to {max_field} T under the 0.785x peak-fiber surrogate; "
                   "the 0.26x/0.785x factor contradiction is unresolved until real FEA "
                   "(ANSYS/COMSOL/Elmer) adjudicates — result is surrogate-tagged [T]."),
        evidence={"max_buildable_field_T": max_field,
                  "peak_fiber_factor": 0.785,
                  "retired_by": ADAPTERS["struct_fea"].retired_by},
    )

    print(f"peak-fiber factor : 0.785 [T surrogate]")
    print(f"max buildable field: {max_field} T (<= {REBCO_ALLOWABLE_MPA} MPa)")
    print(f"verdict           : {v['decision']}")
    print(f"outputs           : {OUT}")
    return study


if __name__ == "__main__":
    main()
