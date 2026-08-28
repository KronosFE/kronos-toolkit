"""Worked example 1 — tritium-exporter push (scan -> confirm -> surplus).

Retrofit of PHASE 3 / HYPERION / UPSIDE / exporter_push.py into the toolkit.
Exercises: core (surplus law) + neutronics (analytic/OpenMC TBR) + report
(scaffold, CSV, manifest, verdict). Public-clean by construction.

Run:  python study_template/tritium_exporter_push.py
Reproduces: T_burn ~ 4.97 kg-T/fpy and the net-TBR -> surplus ladder.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kronos_toolkit.core import surplus_kg_per_fpy, tritium_burn_rate
from kronos_toolkit.neutronics import tbr
from kronos_toolkit.report import Study

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_results", "tritium_exporter_push")

# Net-TBR ladder to scan (the exporter push: how much surplus at each net TBR).
NET_TBR_LADDER = [1.05, 1.10, 1.20, 1.34, 1.50, 1.65, 1.80]
EXPORTER_THRESHOLD = 1.0     # kg-T/fpy above which the plant is a net exporter


def build_rows():
    rows = []
    t_burn = tritium_burn_rate()      # ~4.77 kg-T/fpy at 85.0 MW
    for net in NET_TBR_LADDER:
        surplus = surplus_kg_per_fpy(net)
        rows.append(dict(
            net_tbr=net,
            t_burn_kg_fpy=t_burn,
            surplus_kg_fpy=surplus,
            exporter=("yes" if surplus >= EXPORTER_THRESHOLD else "no"),
        ))
    return rows


def main(stamp=None):
    study = Study("tritium_exporter_push", out_dir=OUT, public=True, stamp=stamp)
    study.pre_register(
        question="At what net TBR does the breeder become a tritium exporter?",
        hypothesis="Surplus is linear in (net_TBR - 1); exporter above net_TBR ~ 1.2.",
        method="surplus law (core) over a net-TBR ladder; blanket TBR cross-check (neutronics).",
        gate="net exporter = surplus >= 1.0 kg-T/fpy",
        tags=["breeder", "tritium", "surplus"],
    )

    rows = build_rows()
    study.add_rows(rows, columns=["net_tbr", "t_burn_kg_fpy",
                                  "surplus_kg_fpy", "exporter"])

    # Independent blanket cross-check via the neutronics API (analytic or OpenMC).
    blanket = tbr()
    exporters = [r["net_tbr"] for r in rows if r["exporter"] == "yes"]
    first_exporter = min(exporters) if exporters else None

    study.to_csv()
    study.manifest(anchors={"t_burn_kg_fpy": {"value": 4.97, "atol": 0.05}})
    v = study.verdict(
        "CONDITIONAL",
        rationale=(f"Net exporter from net_TBR >= {first_exporter}; but the frozen "
                   f"3-D blanket gives net TBR {blanket.value['net_tbr']:.3f} < 1, "
                   "so surplus is conditional on closing the blanket."),
        evidence={"first_exporter_net_tbr": first_exporter,
                  "blanket_net_tbr": blanket.value["net_tbr"],
                  "blanket_tag": blanket.tag},
    )

    print(f"T_burn         : {rows[0]['t_burn_kg_fpy']:.3f} kg-T/fpy")
    print(f"first exporter : net_TBR = {first_exporter}")
    print(f"blanket net TBR: {blanket.value['net_tbr']:.4f} [{blanket.tag}]")
    print(f"verdict        : {v['decision']}")
    print(f"outputs        : {OUT}")
    return study


if __name__ == "__main__":
    main()
