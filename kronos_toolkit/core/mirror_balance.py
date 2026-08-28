"""D-3He mirror power balance evaluator — unified from mirror.py solve_point.

Reproduces the frozen M-45 design point at l_c=440:
Q_E 1.31812, P_fus 4298.5 MW, P_n 233.95 MW, f_n 5.4426%, phi_i 248.75 keV.
"""
import math
import numpy as np
from scipy.optimize import minimize_scalar, brentq
from .constants import (
    M_P, M_E, QE, EPS0, MU0, KEV_J as KEV, MEV_J as MEV,
    ETA_TH, ETA_WP, ETA_DEC,
)
from .reactivities import SV_TABLE, PRODUCTS, R_DHE3, R_DDN, R_DDP, R_DT
from .radiation import (
    p_brems_classic, p_brems_xie_species,
    p_sync_afj, p_sync_trubnikov, p_sync_optically_thin,
)
from .confinement import (
    mirror_mix, mirror_confinement, P_ie, lnL_ei,
)

_GL64 = np.polynomial.legendre.leggauss(64)


def _stix_frac_to_ions(E0_keV, Te_keV, n_d, n_he, ne, A_f, Z_f):
    brack = (n_d * 1.0 / 2.0 + n_he * 4.0 / 3.0) / ne
    Ec = 14.8 * A_f * Te_keV * brack**(2.0 / 3.0)
    u = E0_keV / Ec
    xg, wg = _GL64
    yy = 0.5 * u * (xg + 1.0)
    I = 0.5 * u * float(np.dot(wg, 1.0 / (1.0 + yy**1.5)))
    F_i = I / u
    return float(np.clip(F_i, 0.0, 1.0)), float(Ec)


def _fusion_channels(Ti_keV, n_d, n_he, tau_p_s):
    T = np.array([Ti_keV], dtype=float)
    sv_dhe3 = float(SV_TABLE[R_DHE3][0](T)[0])
    sv_ddn = float(SV_TABLE[R_DDN][0](T)[0])
    sv_ddp = float(SV_TABLE[R_DDP][0](T)[0])
    sv_dt = float(SV_TABLE[R_DT][0](T)[0])

    R_dhe3 = n_d * n_he * sv_dhe3
    R_ddn = 0.5 * n_d * n_d * sv_ddn
    R_ddp = 0.5 * n_d * n_d * sv_ddp

    rate_burn = n_d * sv_dt
    f_T_burn = rate_burn / (rate_burn + 1.0 / tau_p_s)
    R_dt = R_ddp * f_T_burn

    P = {
        R_DHE3: R_dhe3 * PRODUCTS[R_DHE3]["Q"] * MEV,
        R_DDN: R_ddn * PRODUCTS[R_DDN]["Q"] * MEV,
        R_DDP: R_ddp * PRODUCTS[R_DDP]["Q"] * MEV,
        R_DT: R_dt * PRODUCTS[R_DT]["Q"] * MEV,
    }
    rates = {R_DHE3: R_dhe3, R_DDN: R_ddn, R_DDP: R_ddp, R_DT: R_dt}

    P_fus = sum(P.values())
    P_n = (R_ddn * PRODUCTS[R_DDN]["En"] + R_dt * PRODUCTS[R_DT]["En"]) * MEV
    return dict(P=P, rates=rates, P_fus=P_fus, P_n=P_n,
                f_n=P_n / P_fus if P_fus > 0 else 0.0,
                f_T_burn=f_T_burn, sv_dhe3=sv_dhe3, sv_ddn=sv_ddn,
                sv_ddp=sv_ddp, sv_dt=sv_dt, He3_breed_rate=R_ddn)


def _charged_to_electrons(ch, Ti_keV, Te_keV, n_d, n_he, ne):
    P_e = 0.0
    P_i = 0.0
    detail = []
    for rxn, R in ch["rates"].items():
        if R <= 0:
            continue
        for (E_MeV, Z, A) in PRODUCTS[rxn]["charged"]:
            F_i, Ec = _stix_frac_to_ions(E_MeV * 1e3, Te_keV, n_d, n_he, ne, A, Z)
            p = R * E_MeV * MEV
            P_i += p * F_i
            P_e += p * (1.0 - F_i)
            detail.append(dict(rxn=rxn, E_MeV=E_MeV, A=A, Ec_keV=Ec, F_ion=F_i,
                               P_MWm3=p / 1e6))
    return P_e, P_i, detail


def _evaluate_at_Te(Te, ne, x_he3, Ti_keV, a_c, l_c, beta_c, B_m,
                    n_plug_over_n_c, Rwall=0.90, eta_dec=ETA_DEC,
                    sync_model="AFJ", eta_alpha=0.0, q_endwall_limit=2.5,
                    expander_ratio=None):
    Te = float(Te)
    n_d, n_he, ni, Zeff = mirror_mix(ne, x_he3)
    sp = [(n_d, 1.0, 2.0), (n_he, 2.0, 3.0)]
    V = math.pi * a_c**2 * l_c
    A_wall = 2.0 * math.pi * a_c * l_c
    R0_eq = l_c / (2.0 * math.pi)
    psyn_f = p_sync_afj if sync_model == "AFJ" else p_sync_trubnikov

    p = (ne * Te + ni * Ti_keV) * KEV
    B = math.sqrt(2.0 * MU0 * p / beta_c)

    conf = mirror_confinement(ne, x_he3, Ti_keV, Te, a_c, l_c, B, B_m,
                               beta_c, n_plug_over_n_c)
    tau_p = conf["tau_c"]
    if not (tau_p > 0):
        return dict(feasible=False, reason="plug model invalid at this Te",
                    Te_keV=Te, B_0c=B, Q_E=np.nan, P_fus_MW=np.nan,
                    past_valid=conf["past_valid"])

    ch = _fusion_channels(Ti_keV, n_d, n_he, tau_p)
    P_e_ch, P_i_ch, prod_detail = _charged_to_electrons(ch, Ti_keV, Te, n_d, n_he, ne)
    P_charged = ch["P_fus"] - ch["P_n"]

    P_chan = eta_alpha * (P_e_ch + P_i_ch)
    P_e_ch_eff = (1.0 - eta_alpha) * P_e_ch
    P_i_ch_eff = (1.0 - eta_alpha) * P_i_ch + P_chan

    pb = float(p_brems_classic(ne, Te, Zeff))
    pb_xie = float(p_brems_xie_species(ne, Te, [(n_d / ne, 1.0), (n_he / ne, 2.0)]))
    ps_afj = p_sync_afj(R0_eq, a_c, 1.0, B, ne, Te, Rwall) / V
    ps_tru = p_sync_trubnikov(R0_eq, a_c, 1.0, B, ne, Te, Rwall) / V
    ps_thin = p_sync_optically_thin(R0_eq, a_c, 1.0, B, ne, Te) / V
    ps = {"AFJ": ps_afj, "Trubnikov": ps_tru, "thin": ps_thin}[sync_model]

    p_a0_chk = 6.04e3 * (a_c * 1.0e-20 * ne) / B
    afj_in_range = bool(10.0 <= Te <= 100.0 and 1e2 <= p_a0_chk <= 1e4)

    P_i_ax = 1.5 * ni * Ti_keV * KEV / tau_p
    P_e_ax = 1.5 * ne * Te * KEV / tau_p
    P_ax = P_i_ax + P_e_ax

    P_iee = P_ie(ne, sp, Te, Ti_keV)
    P_aux_i = P_i_ax + P_iee - P_i_ch_eff
    P_aux_e = pb + ps + P_e_ax - P_iee - P_e_ch_eff
    P_heat = max(P_aux_i, 0.0) + max(P_aux_e, 0.0)

    P_thermal = pb + ps + ch["P_n"] + (1.0 - eta_dec) * P_ax
    P_out = eta_dec * P_ax + ETA_TH * P_thermal
    P_in = P_heat / ETA_WP
    Q_E = P_out / P_in if P_in > 0 else np.inf
    Q_p = ch["P_fus"] / P_heat if P_heat > 0 else np.inf

    P_exh = P_ax + pb + ps + ch["P_n"]
    f_dir = P_ax / P_exh if P_exh > 0 else 0.0

    UK = 1.5 * (ne * Te + ni * Ti_keV) * KEV
    P_rad = pb + ps

    q_wall = (pb + ps + ch["P_n"]) * V / A_wall / 1e6
    A_throat = math.pi * a_c**2 * (B / B_m)
    A_end_min = 2.0 * (P_ax * V / 1e6) / q_endwall_limit
    exp_req = A_end_min / (2.0 * A_throat) if A_throat > 0 else np.inf
    if expander_ratio is not None:
        A_end = 2.0 * A_throat * expander_ratio
        q_end = (P_ax * V / 1e6) / A_end
    else:
        A_end, q_end = A_end_min, q_endwall_limit

    return dict(
        feasible=True, reason="",
        ne=ne, x_he3=x_he3, Ti_keV=Ti_keV, a_c=a_c, l_c=l_c, beta_c=beta_c,
        B_m=B_m, n_plug_over_n_c=n_plug_over_n_c, eta_dec=eta_dec,
        eta_alpha=eta_alpha, sync_model=sync_model, Rwall=Rwall,
        Te_keV=Te, B_0c=B, p_MPa=p / 1e6, V_m3=V, A_wall_m2=A_wall, R0_eq=R0_eq,
        n_D=n_d, n_He3=n_he, n_i=ni, Zeff=Zeff, past_valid=conf["past_valid"],
        R_mc=conf["R_mc"], R_vac=B_m / B, phi_i_keV=conf["phi_i_keV"],
        phi_i_over_Ti=conf["phi_i_over_Ti"],
        phi_e_over_Te_frank=conf["phi_e_over_Te"],
        tau_p_s=tau_p, tau_past_s=conf["tau_past"], tau_f_s=conf["tau_f"],
        tau_rho_s=conf["tau_rho"], rho_i_m=conf["rho_i"],
        a_over_rho=a_c / conf["rho_i"], n_tau=ne * tau_p,
        P_fus_MWm3=ch["P_fus"] / 1e6, P_fus_MW=ch["P_fus"] * V / 1e6,
        P_n_MW=ch["P_n"] * V / 1e6, f_n=ch["f_n"], f_T_burn=ch["f_T_burn"],
        P_DHe3_MW=ch["P"][R_DHE3] * V / 1e6, P_DDn_MW=ch["P"][R_DDN] * V / 1e6,
        P_DDp_MW=ch["P"][R_DDP] * V / 1e6, P_DT_MW=ch["P"][R_DT] * V / 1e6,
        He3_breed_per_s=ch["He3_breed_rate"] * V,
        P_brems_MW=pb * V / 1e6, P_brems_xie_MW=pb_xie * V / 1e6,
        P_sync_MW=ps * V / 1e6, P_sync_afj_MW=ps_afj * V / 1e6,
        P_sync_tru_MW=ps_tru * V / 1e6, P_sync_thin_MW=ps_thin * V / 1e6,
        afj_in_range=afj_in_range, p_a0=p_a0_chk,
        P_rad_MW=P_rad * V / 1e6,
        f_rad=P_rad / ch["P_fus"] if ch["P_fus"] > 0 else np.inf,
        P_ax_MW=P_ax * V / 1e6, P_i_ax_MW=P_i_ax * V / 1e6,
        P_e_ax_MW=P_e_ax * V / 1e6, P_ie_MW=P_iee * V / 1e6,
        P_e_charged_MW=P_e_ch * V / 1e6, P_i_charged_MW=P_i_ch * V / 1e6,
        frac_charged_to_e=P_e_ch / (P_e_ch + P_i_ch) if (P_e_ch + P_i_ch) > 0 else np.nan,
        P_aux_i_MW=P_aux_i * V / 1e6, P_aux_e_MW=P_aux_e * V / 1e6,
        P_heat_MW=P_heat * V / 1e6,
        P_out_MWe=P_out * V / 1e6, P_in_MWe=P_in * V / 1e6, Q_E=Q_E, Q_p=Q_p,
        recirc=P_in / P_out if P_out > 0 else np.inf,
        f_dir=f_dir,
        q_wall_MWm2=q_wall, A_end_m2=A_end, q_end_MWm2=q_end,
        expander_required=exp_req, A_throat_m2=A_throat,
        prod_detail=prod_detail,
    )


def solve_mirror(ne, x_he3, Ti_keV, a_c, l_c, beta_c, B_m,
                 n_plug_over_n_c, Te_keV=None, Te_mode="maxQE", n_te=60, **kw):
    """Choose Te, then evaluate. Same interface as mirror.py solve_point."""
    common = dict(ne=ne, x_he3=x_he3, Ti_keV=Ti_keV, a_c=a_c, l_c=l_c,
                  beta_c=beta_c, B_m=B_m, n_plug_over_n_c=n_plug_over_n_c, **kw)
    if Te_keV is not None:
        out = _evaluate_at_Te(Te_keV, **common)
        out["Te_mode"] = "fixed"
        return out

    grid = np.linspace(1.0, Ti_keV * 0.999, n_te)
    res = [_evaluate_at_Te(float(t), **common) for t in grid]
    ok = [(t, r) for t, r in zip(grid, res) if r.get("feasible")]
    if not ok:
        return dict(feasible=False, reason="no valid plug branch at any Te<=Ti",
                    ne=ne, x_he3=x_he3, Ti_keV=Ti_keV, a_c=a_c, l_c=l_c,
                    beta_c=beta_c, B_m=B_m, n_plug_over_n_c=n_plug_over_n_c,
                    Q_E=np.nan, P_fus_MW=np.nan, Te_mode=Te_mode)

    T = np.array([t for t, _ in ok])
    if Te_mode == "selfheat":
        aux = np.array([r["P_aux_e_MW"] for _, r in ok])
        s = np.sign(aux)
        cross = np.where(np.diff(s) != 0)[0]
        if len(cross):
            i = cross[0]
            f = lambda t: _evaluate_at_Te(float(t), **common)["P_aux_e_MW"]
            Te = brentq(f, T[i], T[i + 1], xtol=1e-8)
            out = _evaluate_at_Te(Te, **common)
            out["Te_mode"] = "selfheat"
            out["Te_selfheat_exists"] = True
            return out
        qs = np.array([r["Q_E"] for _, r in ok])
        Te = float(T[int(np.nanargmax(qs))])
        out = _evaluate_at_Te(Te, **common)
        out["Te_mode"] = "maxQE (no selfheat root)"
        out["Te_selfheat_exists"] = False
        return out

    qs = np.array([r["Q_E"] for _, r in ok])
    i0 = int(np.nanargmax(qs))
    lo = T[max(i0 - 1, 0)]
    hi = T[min(i0 + 1, len(T) - 1)]
    g_fn = lambda t: -_evaluate_at_Te(float(t), **common)["Q_E"]
    m = minimize_scalar(g_fn, bounds=(lo, hi), method="bounded",
                        options=dict(xatol=1e-6))
    Te = float(m.x) if m.success and -m.fun >= qs[i0] else float(T[i0])
    out = _evaluate_at_Te(Te, **common)
    out["Te_mode"] = "maxQE"
    aux = np.array([r["P_aux_e_MW"] for _, r in ok])
    out["Te_selfheat_exists"] = bool((np.sign(aux)[:-1] != np.sign(aux)[1:]).any())
    return out
