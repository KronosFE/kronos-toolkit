"""Tritium bookkeeping and surplus law.

Surplus law: (net_TBR - 1) * T_burn [kg-T/fpy], where T_burn comes from P_fus.
Anchors: 1.34 -> 1.69, 1.80 -> 3.98 kg-T/fpy (at P_fus = 88.7 MW).
"""
from .constants import M_T_KG, YEAR_S, E_DT, MEV_J

P_FUS_FROZEN_MW = 88.7
E_DT_MEV = 17.59


def tritium_burn_rate(p_fus_mw=P_FUS_FROZEN_MW):
    """Tritium consumption rate [kg-T/fpy] at given fusion power."""
    reactions_per_s = (p_fus_mw * 1e6) / (E_DT_MEV * 1e6 * MEV_J / 1e6)
    return reactions_per_s * M_T_KG * YEAR_S


def surplus_kg_per_fpy(net_tbr, p_fus_mw=P_FUS_FROZEN_MW):
    """Net tritium produced above self-consumption [kg-T/fpy]."""
    return (net_tbr - 1.0) * tritium_burn_rate(p_fus_mw)
