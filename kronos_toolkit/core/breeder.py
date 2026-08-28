"""DT breeder evaluator — unified from dt_evaluator.py + kronos_clean.py.

Reproduces config 22021: Q 3.076, P_fus 85.04 MW, I_p 9.66 MA.
"""
import numpy as np
from .constants import (
    MU0, KEV_J, MEV_J, SYNC_CAL, BETAN_NOWALL, BETAN_RWM, B_COIL_DEMO,
    INBOARD_BUILD, DPA_PER_MWYR, DUTY_LO, DUTY_HI,
    EN_DDN, EN_DT, E_DDP, E_DDN, E_DT, E_D3HE,
    M_T_KG, YEAR_S, RHO,
)
from .reactivities import sigmav
from .radiation import p_brems_xie, p_sync_breeder
from .profiles import (
    parab, vol_avg, kappa_perim, plasma_volume, n_greenwald_1e20,
)
from .confinement import tau_E_IPB98y2, bootstrap_fraction


def _ip_from_q95(R0, a, B0, q95, kappa, delta):
    eps = a / R0
    shape = (1 + kappa**2 * (1 + 2 * delta**2 - 1.2 * delta**3)) / 2.0
    return (5.0 * a**2 * B0 / (R0 * q95)) * shape * (1.17 - 0.65 * eps) / (1 - eps**2)**2


def _geom(R0, A, kappa, B0, q95, delta=-0.30):
    a = R0 / A
    Ip = _ip_from_q95(R0, a, B0, q95, kappa, delta)
    R_cp = R0 - a - INBOARD_BUILD
    B_peak = B0 * R0 / R_cp if R_cp > 0 else np.inf
    L_pol = 2 * np.pi * a * kappa_perim(kappa)
    return dict(a=a, eps=a / R0, Ip_MA=Ip, R_cp=R_cp, B_peak=B_peak,
                L_pol=L_pol, V_m3=plasma_volume(R0, a, kappa), delta=delta)


def _ion_mix(fuel, ne, f_he4=0.0, f_he3_ash=0.0, x_he3=0.0):
    n_he4 = f_he4 * ne
    n_he3 = f_he3_ash * ne
    ne_fuel = ne - 2 * n_he4 - 2 * n_he3
    ne_fuel = max(ne_fuel, 0.0) if np.isscalar(ne_fuel) else np.maximum(ne_fuel, 0.0)
    if fuel == "DD":
        nD, nT = ne_fuel, 0.0
    elif fuel == "DT":
        nD = nT = 0.5 * ne_fuel
    elif fuel == "catDD":
        nD, nT = ne_fuel, 0.0
    elif fuel == "DHe3":
        # ---- additive D-He3 fuel branch (BR-L1-A3, 2026-08-25) ----
        # Same convention as core.confinement.mirror_mix: x_he3 = n_He3 / n_ion(fuel),
        # quasineutral with Z_He3 = 2; Zeff = sum(n_j Z_j^2)/n_e (standard form).
        # Early return: DT/DD/catDD paths below are untouched.
        ni_fuel = ne_fuel / (1.0 + x_he3)
        n_he3 = n_he3 + x_he3 * ni_fuel   # fuel He-3 on top of any He-3 ash
        nD, nT = (1.0 - x_he3) * ni_fuel, 0.0
        n_ion = nD + n_he4 + n_he3
        Zeff = (nD + 4 * n_he4 + 4 * n_he3) / np.maximum(ne, 1e-30)
        return dict(nD=nD, nT=nT, n_he4=n_he4, n_he3=n_he3, n_ion=n_ion, Zeff=Zeff)
    else:
        raise ValueError(fuel)
    n_ion = nD + nT + n_he4 + n_he3
    Zeff = (nD + nT + 4 * n_he4 + 4 * n_he3) / np.maximum(n_ion, 1e-30)
    return dict(nD=nD, nT=nT, n_he4=n_he4, n_he3=n_he3, n_ion=n_ion, Zeff=Zeff)


def _reaction_rates(fuel, mix, T_keV, tau_p=2.0):
    nD, nT = mix["nD"], mix["nT"]
    svp = sigmav("DDp", T_keV)
    svn = sigmav("DDn", T_keV)
    R_DDp = 0.5 * nD**2 * svp
    R_DDn = 0.5 * nD**2 * svn
    if fuel == "DT":
        R_DT = nD * nT * sigmav("DT", T_keV)
        R_D3He = np.zeros_like(np.asarray(R_DT, float))
    elif fuel == "catDD":
        R_DT = R_DDp.copy()
        R_D3He = R_DDn.copy()
    elif fuel == "DHe3":
        # ---- additive D-He3 fuel branch (BR-L1-A3, 2026-08-25) ----
        # Primary D+He3 -> p + alpha (all charged); D-D side reactions kept as
        # computed above; secondary burnup of D-D(p) tritons uses the SAME
        # burn-fraction law as the DD mode / mirror engine (_fusion_channels):
        # f_T = tau_p*nD*<sv>_DT / (1 + tau_p*nD*<sv>_DT), applied pointwise.
        R_D3He = nD * mix["n_he3"] * sigmav("D3He", T_keV)
        R_DT = R_DDp * _burn_fraction_direct(nD, T_keV, tau_p)
    else:
        R_DT = np.zeros_like(np.asarray(R_DDp, float))
        R_D3He = np.zeros_like(np.asarray(R_DDp, float))
    return R_DDp, R_DDn, R_DT, R_D3He


def _power_density(R_DDp, R_DDn, R_DT, R_D3He):
    p_tot = (R_DDp * E_DDP + R_DDn * E_DDN + R_DT * E_DT + R_D3He * E_D3HE) * MEV_J
    p_n = (R_DDn * EN_DDN + R_DT * EN_DT) * MEV_J
    return p_tot, p_n


def _burn_fraction_direct(nD, T_keV, tau_p):
    rate = nD * sigmav("DT", T_keV)
    return (tau_p * rate) / (1.0 + tau_p * rate)


def evaluate_breeder(fuel, R0, A, kappa, B0, q95, fG, Ti0, TBR_dt, TBR_dd=1.0,
                     H98=1.0, tau_p=2.0, alphaT=1.0, alphaN=0.0, f_he4=0.0,
                     sync_cal=None, cf=1.0, delta=-0.30, x_he3=0.35):
    """One breeder configuration -> one row dict. Nothing frozen; every field computed."""
    sync_cal = SYNC_CAL if sync_cal is None else sync_cal
    g = _geom(R0, A, kappa, B0, q95, delta)
    a, Ip, V = g["a"], g["Ip_MA"], g["V_m3"]

    nG20 = n_greenwald_1e20(Ip, a)
    ne_bar = fG * nG20 * 1e20

    Tp = parab(RHO, Ti0, 0.02, alphaT)
    nsh = parab(RHO, 1.0, 0.0, alphaN)
    nsh = nsh / (np.trapezoid(nsh * RHO, RHO) / np.trapezoid(RHO, RHO))
    ne_p = ne_bar * nsh

    mix = _ion_mix(fuel, ne_p, f_he4=f_he4, x_he3=x_he3)  # x_he3 used only by fuel="DHe3"
    Zeff_p = mix["Zeff"]
    Zeff = vol_avg(Zeff_p)

    R_DDp, R_DDn, R_DT, R_D3He = _reaction_rates(fuel, mix, Tp, tau_p=tau_p)  # tau_p used only by fuel="DHe3"
    p_fus, p_n = _power_density(R_DDp, R_DDn, R_DT, R_D3He)
    P_fus = vol_avg(p_fus) * V / 1e6
    P_n = vol_avg(p_n) * V / 1e6
    f_n = P_n / P_fus if P_fus > 0 else np.nan

    P_br = vol_avg(p_brems_xie(ne_p, Tp, Zeff_p)) * V / 1e6
    P_sy = vol_avg(p_sync_breeder(ne_p, Tp, B0, a, kappa, R0)) * V * sync_cal
    P_rad = P_br + P_sy
    P_chg = P_fus - P_n

    n19 = ne_bar / 1e19
    W_of_P = lambda P: (tau_E_IPB98y2(Ip, B0, n19, P, R0, g["eps"], kappa,
                                       M_amu=2.5 if fuel == "DT" else
                                       (2.0 + x_he3 if fuel == "DHe3" else 2.0), H=H98) * P)
    W_th = 1.5 * vol_avg(2 * ne_p * Tp * KEV_J) * V / 1e6
    lo, hi = 1e-3, 1e5
    for _ in range(200):
        mid = np.sqrt(lo * hi)
        if W_of_P(mid) < W_th:
            lo = mid
        else:
            hi = mid
    P_heat = np.sqrt(lo * hi)
    P_aux = max(P_heat - P_chg, 0.0)
    tau_E = tau_E_IPB98y2(Ip, B0, n19, P_heat, R0, g["eps"], kappa,
                          M_amu=2.5 if fuel == "DT" else
                          (2.0 + x_he3 if fuel == "DHe3" else 2.0), H=H98)
    Q = P_fus / P_aux if P_aux > 0 else np.inf

    p_bar = vol_avg(2 * ne_p * Tp * KEV_J)
    beta_t = 2 * MU0 * p_bar / B0**2
    betaN = beta_t * 100 * a * B0 / Ip

    ni_p = mix["n_ion"]
    f_sau, f_lo, f_hi, beta_p = bootstrap_fraction(
        R0, a, kappa, B0, Ip, q95, ne_p, Tp, Tp, ni_p, Zeff, g["L_pol"])
    Ip_driven = Ip * (1.0 - f_sau)

    fbd = vol_avg(_burn_fraction_direct(mix["nD"], Tp, tau_p)) if fuel == "DD" else 0.0
    T_kg = float(vol_avg(R_DDp * (1 - fbd) + TBR_dd * R_DDn + TBR_dt * R_DT - R_DT)
                 * V * M_T_KG * YEAR_S * cf)

    A_wall = 2 * np.pi * R0 * g["L_pol"]
    wall = P_n / A_wall
    dpa = wall * DPA_PER_MWYR

    return dict(fuel=fuel, x_he3=(x_he3 if fuel == "DHe3" else 0.0),
                TBR_dt=TBR_dt, TBR_dd=TBR_dd, B0=B0, R0=R0, A=A,
                a=a, kappa=kappa, q95=q95, fG=fG, Ti0=Ti0, H98=H98, tau_p=tau_p,
                B_peak=g["B_peak"], R_cp=g["R_cp"], V_m3=V, ne_bar=ne_bar,
                nG20=nG20, Zeff=Zeff, P_fus_MW=P_fus, P_n_MW=P_n, f_n=f_n,
                P_br_MW=P_br, P_sync_MW=P_sy, P_rad_MW=P_rad, P_chg_MW=P_chg,
                P_aux_MW=P_aux, tau_E=tau_E, W_MJ=W_th, Q=Q, betaN=betaN,
                beta_t=beta_t, beta_p=beta_p, Ip_MA=Ip, f_bs=f_sau,
                f_bs_lo=f_lo, f_bs_hi=f_hi, Ip_driven_MA=Ip_driven,
                f_T_burn_direct=fbd, T_kg_yr=T_kg, wall_MW_m2=wall,
                dpa_per_fpy=dpa,
                on_duty=bool(DUTY_LO <= T_kg <= DUTY_HI),
                beta_ok_nowall=bool(betaN < BETAN_NOWALL),
                beta_ok_rwm=bool(betaN < BETAN_RWM),
                coil_ok=bool(g["B_peak"] <= B_COIL_DEMO),
                density_ok=bool(fG <= 1.0))
