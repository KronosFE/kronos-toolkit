"""Confinement models: IPB98(y,2), Sauter bootstrap, Pastukhov mirror confinement.

IPB98(y,2) + bootstrap: used by the breeder engine (from kronos_clean + dt_evaluator).
Pastukhov + Frank: used by the mirror engine (from mirror.py).
"""
import math
import numpy as np
from scipy.optimize import brentq
from .constants import (MU0, KEV_J, QE, M_P, M_E, EPS0, RHO)
from .profiles import (trapped_fraction, kappa_perim, vol_avg)


# ============================================================================
# IPB98(y,2) energy confinement time (breeder)
# ============================================================================
def tau_E_IPB98y2(Ip_MA, B_T, n19, P_MW, R0_m, eps, kappa_a, M_amu=2.0, H=1.0):
    """IPB98(y,2) ELMy H-mode energy confinement time [s]."""
    return (0.0562 * H * Ip_MA**0.93 * B_T**0.15 * P_MW**-0.69 * n19**0.41
            * M_amu**0.19 * R0_m**1.97 * eps**0.58 * kappa_a**0.78)


# ============================================================================
# Sauter bootstrap current (breeder)
# ============================================================================
def _F31(X, Z):
    return ((1 + 1.4 / (Z + 1)) * X - 1.9 / (Z + 1) * X**2
            + 0.3 / (Z + 1) * X**3 + 0.2 / (Z + 1) * X**4)


def _F32ee(X, Z):
    return ((0.05 + 0.62 * Z) / (Z * (1 + 0.44 * Z)) * (X - X**4)
            + 1 / (1 + 0.22 * Z) * (X**2 - X**4 - 1.2 * (X**3 - X**4))
            + 1.2 / (1 + 0.5 * Z) * X**4)


def _F32ei(X, Z):
    return (-(0.56 + 1.93 * Z) / (Z * (1 + 0.44 * Z)) * (X - X**4)
            + 4.95 / (1 + 2.48 * Z) * (X**2 - X**4 - 0.55 * (X**3 - X**4))
            - 1.2 / (1 + 0.5 * Z) * X**4)


def bootstrap_fraction(R0, a, kappa, B0, Ip_MA, q95, ne_p, Te_p, Ti_p, ni_p,
                        Zeff, L_pol):
    """Sauter bootstrap fraction, two independent estimates, both against the same Ip.

    Returns (f_bs_sauter, f_bs_lo, f_bs_hi, beta_p).
    """
    r = RHO * a
    eps_r = np.maximum(r / R0, 1e-6)
    Ip_A = Ip_MA * 1e6

    q_prof = 1.0 + (q95 - 1.0) * RHO**2
    I_shape = RHO**2 / np.maximum(q_prof, 1e-3)
    I_encl = Ip_A * I_shape / I_shape[-1]
    Bp = MU0 * I_encl / (L_pol * RHO)
    Bp = np.where(RHO > 0, Bp, np.nan)

    ft = trapped_fraction(eps_r)
    Te_eV, Ti_eV = Te_p * 1e3, Ti_p * 1e3
    lnLe = 31.3 - np.log(np.sqrt(ne_p) / Te_eV)
    lnLi = 30.0 - np.log(Zeff**3 * np.sqrt(ni_p) / Ti_eV**1.5)
    nue = (6.921e-18 * R0 * q_prof * ne_p * Zeff * lnLe) / (eps_r**1.5 * Te_eV**2)
    nui = (4.900e-18 * R0 * q_prof * ni_p * Zeff**4 * lnLi) / (eps_r**1.5 * Ti_eV**2)

    X31 = ft / (1 + (1 - 0.1 * ft) * np.sqrt(nue) + 0.5 * (1 - ft) * nue / Zeff)
    X32e = ft / (1 + 0.26 * (1 - ft) * np.sqrt(nue)
                 + 0.18 * (1 - 0.37 * ft) * nue / np.sqrt(Zeff))
    X32i = ft / (1 + (1 + 0.6 * ft) * np.sqrt(nue)
                 + 0.85 * (1 - 0.37 * ft) * nue * (1 + Zeff))
    X34 = ft / (1 + (1 - 0.1 * ft) * np.sqrt(nue) + 0.5 * (1 - 0.5 * ft) * nue / Zeff)

    L31 = _F31(X31, Zeff)
    L32 = _F32ee(X32e, Zeff) + _F32ei(X32i, Zeff)
    L34 = _F31(X34, Zeff)
    a0 = -1.17 * (1 - ft) / (1 - 0.22 * ft - 0.19 * ft**2)
    alpha = ((a0 + 0.25 * (1 - ft**2) * np.sqrt(nui)) / (1 + 0.5 * np.sqrt(nui))
             + 0.315 * nui**2 * ft**6) / (1 + 0.15 * nui**2 * ft**6)

    pe = ne_p * Te_p * KEV_J
    pi_ = ni_p * Ti_p * KEV_J
    p = pe + pi_
    d = lambda y: np.gradient(y, r)
    jbs = -(1.0 / Bp) * (L31 * d(p) + L32 * pe * d(np.log(Te_p))
                          + L34 * alpha * pi_ * d(np.log(Ti_p)))
    jbs = np.nan_to_num(jbs)
    I_bs = np.trapezoid(jbs * (2 * np.pi * r * kappa), r)
    f_sauter = float(np.clip(I_bs / Ip_A, 0.0, 1.0))

    p_bar = np.trapezoid(p * RHO, RHO) / np.trapezoid(RHO, RHO)
    Bp_bar = MU0 * Ip_A / L_pol
    beta_p = 2 * MU0 * p_bar / Bp_bar**2
    eps = a / R0
    f_lo = float(np.clip(0.7 * np.sqrt(eps) * beta_p, 0, 1))
    f_hi = float(np.clip(1.2 * np.sqrt(eps) * beta_p, 0, 1))
    return f_sauter, f_lo, f_hi, beta_p


# ============================================================================
# Pastukhov / Frank mirror confinement
# ============================================================================
def lnL_ei(ne, Te_keV):
    return 24.0 - np.log(np.sqrt(ne * 1e-6) / (Te_keV * 1e3))


def tau_eq_ie(ni, Z, A, Te_keV, Ti_keV, lnL):
    """Braginskii ion-electron energy equilibration time [s]."""
    mi = A * M_P
    Te = Te_keV * 1e3 * QE
    Ti = Ti_keV * 1e3 * QE
    num = 3.0 * mi * M_E * (4 * np.pi * EPS0)**2 * (Te / M_E + Ti / mi)**1.5
    den = 8.0 * np.sqrt(2 * np.pi) * ni * (Z * QE**2)**2 * lnL
    return num / den


def P_ie(ne, species, Te_keV, Ti_keV):
    """Ion->electron collisional power transfer [W/m^3].
    species = [(n_j, Z_j, A_j), ...]."""
    lnL = float(lnL_ei(ne, Te_keV))
    tot = 0.0
    for ni, Z, A in species:
        tot += 1.5 * ni * (Ti_keV - Te_keV) * 1e3 * QE / tau_eq_ie(ni, Z, A, Te_keV, Ti_keV, lnL)
    return tot


def tau_ii_eff(ni_species, Ti_keV, lnL):
    """Effective ion-ion collision time for a deuteron test ion [s]."""
    mD = 2.0 * M_P
    Ti = Ti_keV * 1e3 * QE
    szz = sum(n * 1.0**2 * Z**2 for (n, Z, A) in ni_species)
    num = 3.0 * math.sqrt(mD) * Ti**1.5 * (4 * math.pi * EPS0)**2
    den = 4.0 * math.sqrt(2 * math.pi) * szz * QE**4 * lnL
    return num / den


def G_pastukhov(x):
    """Frank Eq. (3.5)."""
    s = math.sqrt(1.0 + 1.0 / x)
    return s * math.log((s + 1.0) / (s - 1.0))


def phi_e_over_Te(phi_i_over_Ti, Ti_keV, Te_keV, mi_over_me):
    """Frank Eq. (3.8)."""
    rhs = (math.sqrt(mi_over_me) * (Ti_keV / Te_keV)**1.5
           * phi_i_over_Ti * math.exp(phi_i_over_Ti))
    if rhs <= math.e:
        return 1.0
    f = lambda z: z * math.exp(z) - rhs
    return brentq(f, 1e-6, 200.0, xtol=1e-12)


def mirror_mix(ne, x_he3):
    """Quasineutral D-3He mix."""
    ni = ne / (1.0 + x_he3)
    n_he = x_he3 * ni
    n_d = ni - n_he
    Zeff = (n_d + 4.0 * n_he) / ne
    return n_d, n_he, ni, Zeff


def mirror_confinement(ne, x_he3, Ti_keV, Te_keV, a_c, l_c, B_0c, B_m, beta_c,
                        n_plug_over_n_c, C=None):
    """Frank Eqs. (3.2)-(3.8). Returns tau_c [s] and diagnostics."""
    C = _C_CONF if C is None else C
    n_d, n_he, ni, Zeff = mirror_mix(ne, x_he3)
    sp = [(n_d, 1.0, 2.0), (n_he, 2.0, 3.0)]
    lnL = float(lnL_ei(ne, Te_keV))

    R_mc = B_m / (B_0c * math.sqrt(max(1.0 - beta_c, 1e-6)))
    phi_i = Te_keV * math.log(n_plug_over_n_c)
    r = phi_i / Ti_keV
    t_ii = tau_ii_eff(sp, Ti_keV, lnL)

    x = Ti_keV / (2.0 * phi_i)
    denom = 1.0 + x - x * x
    past_valid = (denom > 0.0) and (r > 0.5)
    if past_valid:
        tau_past = (math.sqrt(math.pi) / 2.0) * t_ii * r * math.exp(r) \
            * G_pastukhov(R_mc) / denom
    else:
        tau_past = 0.0

    m_i_mean = (n_d * 2.0 + n_he * 3.0) * M_P / ni
    v_th = math.sqrt(Ti_keV * 1e3 * QE / (2.0 * m_i_mean))
    tau_f = math.sqrt(math.pi) * R_mc * l_c / v_th * math.exp(r)

    Om = QE * B_0c / m_i_mean
    rho_i = v_th / Om
    tau_rho = 0.25 * (a_c / rho_i)**2 * t_ii

    tau_c = C * (1.0 / (tau_past + tau_f) + 1.0 / tau_rho)**-1
    return dict(tau_c=tau_c, tau_past=tau_past, tau_f=tau_f, tau_rho=tau_rho,
                R_mc=R_mc, phi_i_keV=phi_i, phi_i_over_Ti=r, tau_ii=t_ii,
                rho_i=rho_i, v_th=v_th, past_valid=past_valid,
                phi_e_over_Te=phi_e_over_Te(r, Ti_keV, Te_keV, m_i_mean / M_E))


# ============================================================================
# Confinement calibration (import-time, matching mirror.py)
# ============================================================================
_C_CONF = 1.0
C_CONF_EXPECTED = 0.42838809786283644


def _calibrate_conf():
    """Calibrate C_CONF against Frank Table 2 D-T anchor."""
    global _C_CONF
    a_c, l_c, B_0c, B_m, beta_c = 0.86, 50.0, 3.125, 25.0, 0.55
    ne, Ti, Te = 7.0e19, 57.0, 120.0
    n_plug_over_n_c = 1.60e20 / ne

    # compute NTAU_TANDEM (the Mode G extraction)
    Ti_dt, Te_dt, ne_dt, Q_pub = 57.0, 120.0, 7.0e19, 8.75
    from .reactivities import SV_TABLE, R_DT as _R_DT
    from .radiation import p_brems_classic
    sv_fn, _, Q_dt = SV_TABLE[_R_DT]
    n_d_dt = n_t_dt = 0.5 * ne_dt
    pf = float(n_d_dt * n_t_dt * sv_fn(np.array([Ti_dt]))[0] * Q_dt * 1.602176634e-13)
    P_heat_pub = pf / Q_pub
    sp_dt = [(0.5 * ne_dt, 1, 2.0), (0.5 * ne_dt, 1, 3.0)]
    P_ie_dt = P_ie(ne_dt, sp_dt, Te_dt, Ti_dt)
    W_i = 1.5 * ne_dt * Ti_dt * 1e3 * QE
    tau_eff = W_i / (P_heat_pub - P_ie_dt)
    ntau_tandem = ne_dt * tau_eff
    tau_target = ntau_tandem / ne

    _C_CONF = 1.0
    raw = mirror_confinement(ne, 0.0, Ti, Te, a_c, l_c, B_0c, B_m, beta_c,
                              n_plug_over_n_c, C=1.0)
    _C_CONF = tau_target / raw["tau_c"]
    if not abs(_C_CONF - C_CONF_EXPECTED) <= 1e-12 * C_CONF_EXPECTED:
        raise RuntimeError(
            f"C_CONF = {_C_CONF!r} after calibration; expected {C_CONF_EXPECTED!r}")
    return ntau_tandem


NTAU_TANDEM = _calibrate_conf()
