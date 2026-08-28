"""Frozen anchor values — the numbers the toolkit must reproduce exactly."""

# ============================================================================
# BREEDER — config 22021 from dt_scan.csv (dt_evaluator + kronos_clean)
# 2026-08-24: triangularity corrected to canonical NT delta=-0.30 (studies H7/P6).
#   The prior delta=+0.4 was a legacy Mode-C artifact; anchors below re-derived at
#   -0.30 (reduced-order, H98=1.0). NOTE: final headline Q is pending the CGYRO
#   Dimits/quiet-basin confinement result (may recover above this if H98>1).
# ============================================================================
BREEDER_DP = dict(
    fuel="DT", R0=1.2, A=2.5, kappa=2.0, B0=8.0, q95=3.0,
    fG=0.3, Ti0=15.0, TBR_dt=1.8, TBR_dd=1.0,
    H98=1.0, tau_p=2.0, alphaT=1.0, alphaN=0.0, f_he4=0.05,
    sync_cal=6.51, cf=1.0, delta=-0.30,
)

BREEDER_ANCHORS = dict(
    Q=dict(value=3.0763264804593597, atol=1e-4, key="Q"),
    P_fus_MW=dict(value=85.04057711654414, atol=0.5, key="P_fus_MW"),
    Ip_MA=dict(value=9.65648253968254, atol=0.01, key="Ip_MA"),
    T_kg_yr=dict(value=3.836229108166553, atol=0.01, key="T_kg_yr"),
    f_n=dict(value=0.797119629798747, atol=1e-4, key="f_n"),
)

# ============================================================================
# BURNER — frozen M-45 design point (mirror.py solve_point)
# ============================================================================
BURNER_DP = dict(
    ne=2.6e20, x_he3=0.30, Ti_keV=90.0, a_c=0.86, l_c=440.0,
    beta_c=0.55, B_m=17.0, n_plug_over_n_c=16.0,
)

BURNER_ANCHORS = dict(
    Q_E=dict(value=1.31812, atol=1e-4, key="Q_E"),
    P_fus_MW=dict(value=4298.5, atol=0.5, key="P_fus_MW"),
    P_n_MW=dict(value=233.95, atol=0.2, key="P_n_MW"),
    f_n_pct=dict(value=5.4426, atol=0.01, key="f_n", scale=100),
    phi_i_keV=dict(value=248.75, atol=0.05, key="phi_i_keV"),
)

# ============================================================================
# SURPLUS LAW — (net_TBR - 1) * T_burn
# ============================================================================
SURPLUS_ANCHORS = [
    dict(net_tbr=1.34, expected_kg=1.69, atol=0.02),
    dict(net_tbr=1.80, expected_kg=3.98, atol=0.02),
]

# ============================================================================
# NEUTRONICS — breeder blanket TBR (H1 anchor), analytic surrogate at defaults
# ============================================================================
NEUTRONICS_ANCHORS = dict(
    local_tbr=dict(value=1.1517, atol=1e-3, key="local_tbr"),
    net_tbr=dict(value=0.7424, atol=1e-3, key="net_tbr"),
)
