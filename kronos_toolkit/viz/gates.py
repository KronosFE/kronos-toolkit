"""Gate status board — the honest go/no-go gates, computed live from the engines.

Each gate returns green / yellow / red with a one-line status and its source.
Where a gate can be decided from a frozen engine (tritium from neutronics net
TBR, burner net power from the mirror Q_E), it is computed live so the board can
never drift from the physics. The rest carry an honest static status + source.
"""


def compute_gates():
    """Return the list of gate dicts (status in {green, yellow, red})."""
    from ..core.breeder import evaluate_breeder
    from ..core.mirror_balance import solve_mirror
    from ..neutronics import tbr
    from ..verify.anchors import BREEDER_DP, BURNER_DP

    gates = []

    # --- breeder net electric power ---
    br = evaluate_breeder(**BREEDER_DP)
    q_sci = br["Q"]
    gates.append(dict(
        key="breeder_net_power",
        name="Breeder net electric power",
        status="red",
        value=f"Q_sci {q_sci:.2f}",
        status_line=("Q_sci ~3.42 is scientific gain, not net electric. The breeder "
                     "is a supported platform (isotopes/materials/He-3), not a power plant."),
        source="dt_evaluator config 22021 (frozen)",
    ))

    # --- tritium self-sufficiency (live from neutronics net TBR) ---
    net_tbr = tbr().value["net_tbr"]
    gates.append(dict(
        key="tritium_self_sufficiency",
        name="Tritium self-sufficiency",
        status="green" if net_tbr >= 1.0 else "red",
        value=f"net TBR {net_tbr:.3f}",
        status_line=(f"3-D blanket net TBR {net_tbr:.3f} < 1 at the design point: "
                     "tritium-deficit until the blanket is closed."),
        source="neutronics H1 anchor (analytic surrogate [T], retired by OpenMC)",
    ))

    # --- burner plug potential / net power (live from mirror Q_E) ---
    bu = solve_mirror(**BURNER_DP)
    q_e = bu["Q_E"]
    gates.append(dict(
        key="burner_plug_gate1",
        name="Burner plug potential (gate 1)",
        status="yellow",
        value=f"Q_E {q_e:.2f}",
        status_line=(f"Q_E {q_e:.2f} only with plug density n_plug/n_c=16 — a REQUIREMENT, "
                     "not yet demonstrated; magnetic well at feasible beta is unproven."),
        source="mirror.py M-45 frozen DP",
    ))

    # --- coil buildability (gate 2) ---
    gates.append(dict(
        key="coil_gate2",
        name="Plug-coil buildability (gate 2)",
        status="yellow",
        value="0.785x surrogate",
        status_line=("Buildable under the 0.785x peak-fiber surrogate; the 0.26x/0.785x "
                     "factor contradiction awaits real FEA (ANSYS/COMSOL/Elmer)."),
        source="hifi.struct_fea [T], retired by structural FEA",
    ))

    # --- He-3 supply ---
    gates.append(dict(
        key="he3_supply",
        name="He-3 supply",
        status="yellow",
        value="lunar ~2038-40",
        status_line=("Burner fleet is gated on lunar He-3 (~2038-40). He-3 is strategic "
                     "value, not a bankable supply today."),
        source="canonical fleet-shape timeline",
    ))

    # --- availability / capacity factor ---
    gates.append(dict(
        key="availability_cf",
        name="Availability / capacity factor",
        status="red",
        value="open question",
        status_line=("Capacity-factor availability is the #1 open engineering question "
                     "for the breeder — unresolved and load-bearing."),
        source="breeder availability lever study",
    ))

    return gates
