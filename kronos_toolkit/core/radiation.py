"""Bremsstrahlung and synchrotron radiation models.

Bremsstrahlung: Xie (2024) fitted Gaunt factors (kronos_clean) + classic 5.35e-37 form (mirror).
Synchrotron: AFJ (2001) + Trubnikov/ITER-89 via Zohm (2019) + optically thin bound.
"""
import math
import numpy as np
from .constants import (M_E, C_LIGHT, E_CHG, EPS0, H_PL, K_B, KEV_J, MU0,
                        MEC2_KEV, BREMS_PREF_CLASSIC, ZOHM_RWALL, SIGMA_T, QE)

# ============================================================================
# Bremsstrahlung — Xie (2024) fitted Gaunt factors (breeder engine)
# ============================================================================
_CNR = [0.4302, 24.2255e-5, 0.7546e-5, 0.5282, 0.3301, 0.0911]
_CR = [0.55467, 2.6346, -2.277595, 1.1480, -0.36465, 0.07451,
       -0.00975, 0.0007885, -3.5841e-5, 6.99834e-7]
_CZ = [5.760e4, 3.440, 16.80, 0.1333]
_C0 = 1.0 / (1.0 - _CNR[5])

PREF_BR = (32 * np.pi * E_CHG**6 / (3 * (4 * np.pi * EPS0)**3 * H_PL * M_E * C_LIGHT**3)
           * np.sqrt(2 * np.pi * K_B / (3 * M_E)) * np.sqrt(1e3 * E_CHG / K_B))


def g_ei(t, Z):
    """Xie (2024) electron-ion Gaunt factor. t = Te/(me c^2)."""
    t = np.asarray(t, float); Z = np.asarray(Z, float)
    fnr = (_CNR[0] * (1 - np.exp(-(_CNR[1] * Z**2 / t)**_CNR[3]))
           - (_CNR[0] + _CNR[5]) * np.exp(-(t / (_CNR[2] * Z**2))**_CNR[4]))
    fr = _C0 * sum(_CR[j - 1] * t**j for j in range(1, 11))
    u = 100 * t * np.sqrt(10.0 / Z)
    fz = ((Z / 10.0) * _CZ[0] * u**_CZ[1]) / (np.exp(_CZ[2] * u**_CZ[3]) - 1.0)
    return _C0 * (1.0 + fnr - fz) + fr


def g_ee(t):
    """Xie (2024) electron-electron Gaunt factor."""
    t = np.asarray(t, float)
    Fee = 0.5 * (np.tanh(0.602 * (np.log10(t) + 5.06)) + 1)
    FNR = t * 6 * np.sqrt(3) / (np.sqrt(2) * np.pi) * 0.5 * (
        np.tanh(-2.153 * np.log10(t / 0.43)) + 1)
    return Fee * FNR * (1 + 0.53 * t + 9.48 * t**2 - 0.67 * t**3 + 0.027 * t**4)


def p_brems_xie(ne, Te_keV, Zeff=1.0):
    """Xie (2024) bremsstrahlung [W/m^3]. Used by the breeder engine."""
    t = np.asarray(Te_keV, float) / MEC2_KEV
    return PREF_BR * np.asarray(ne, float)**2 * np.sqrt(Te_keV) * (
        Zeff * g_ei(t, Zeff) + g_ee(t))


# ============================================================================
# Bremsstrahlung — classic relativistic-truncated form (mirror engine)
# ============================================================================
def p_brems_classic(ne, Te_keV, Zeff):
    """Classic 5.35e-37 relativistic-truncated bremsstrahlung [W/m^3]."""
    t = np.asarray(Te_keV) / 511.0
    return BREMS_PREF_CLASSIC * ne * ne * np.sqrt(Te_keV) * (
        Zeff * (1 + 0.7936 * t + 1.874 * t * t) + 2.120022 * t)


# Xie full-species form used in the mirror ledger
_XIE_CNR = [0.4302, 24.2255e-5, 0.7546e-5, 0.5282, 0.3301, 0.0911]
_XIE_CR = [0.55467, 2.6346, -2.277595, 1.1480, -0.36465, 0.07451,
           -0.00975, 0.0007885, -3.5841e-5, 6.99834e-7]
_XIE_C0 = 2.0 * math.sqrt(3.0) / math.pi


def _xie_gei_mirror(t, Z):
    t = np.asarray(t, dtype=float)
    cnr1, cnr2, cnr3, cnr4, cnr5, cnr6 = _XIE_CNR
    f_nr = (cnr1 * (1.0 - np.exp(-((cnr2 * Z**2 / t)**cnr4)))
            - (cnr1 + cnr6) * np.exp(-((t / (cnr3 * Z**2))**cnr5)))
    f_r = _XIE_C0 * sum(_XIE_CR[j] * t**(j + 1) for j in range(10))
    return _XIE_C0 * (1.0 + f_nr) + f_r


def _xie_gee_mirror(t):
    t = np.asarray(t, dtype=float)
    F_ee = 0.5 * (np.tanh(0.602 * (np.log10(t) + 5.06)) + 1.0)
    F_NR = t * (6.0 * math.sqrt(3.0) / (math.sqrt(2.0) * math.pi)) * \
        0.5 * (np.tanh(-2.153 * np.log10(t / 0.43)) + 1.0)
    poly = 1.0 + 0.53 * t + 9.48 * t**2 - 0.67 * t**3 + 0.027 * t**4
    return F_ee * F_NR * poly


def _xie_prefactor():
    e, eps0, h, me, c = QE, EPS0, 6.62607015e-34, M_E, C_LIGHT
    pref = 32.0 * math.pi * e**6 / (3.0 * (4.0 * math.pi * eps0)**3 * h * me * c**3)
    return pref * math.sqrt(2.0 * math.pi * KEV_J / (3.0 * me))


_XIE_PREFACTOR = _xie_prefactor()


def p_brems_xie_species(ne, Te_keV, species):
    """Xie species-resolved bremsstrahlung [W/m^3]. species=[(n_j/n_e, Z_j), ...]."""
    t = Te_keV / 511.0
    ei = sum(frac * Z**2 * _xie_gei_mirror(t, Z) for frac, Z in species)
    return _XIE_PREFACTOR * ne**2 * np.sqrt(Te_keV) * (ei + _xie_gee_mirror(t))


# ============================================================================
# Synchrotron — Albajar-Johner-Granata (2001) + Fidone reflectivity
# ============================================================================
def p_sync_breeder(ne, Te_keV, B_T, a_m, kappa, R0_m, refl=0.8):
    """Cai/Xie system-code synchrotron [W/m^3]. Used by the breeder engine."""
    n20 = np.asarray(ne, float) / 1e20
    a_eff = a_m * np.sqrt(kappa)
    return (4.14e-7 * n20**0.5 * np.asarray(Te_keV, float)**2.5 * B_T**2.5
            * (1.0 - refl)**0.5 * a_eff**-0.5
            * (1.0 + 2.5 * np.asarray(Te_keV, float) / 511.0))


def p_sync_afj(R0, a, kappa, B, ne, Te, Rwall=0.90,
               alpha_n=0.0, alpha_T=0.0, tbeta=2.0):
    """Albajar-Johner-Granata (2001) + Fidone reflectivity [W]."""
    ne0_20 = 1.0e-20 * ne * (1.0 + alpha_n)
    aspect = R0 / a
    p_a0 = 6.04e3 * (a * ne0_20) / B
    g_function = 0.93 * (1.0 + 0.85 * math.exp(-0.82 * aspect))
    k_function = ((alpha_n + 3.87 * alpha_T + 1.46)**-0.79
                  * (1.98 + alpha_T)**1.36
                  * tbeta**2.14
                  * (tbeta**1.53 + 1.87 * alpha_T - 0.16)**-1.33)
    dum = (1.0 + 0.12 * (Te / p_a0**0.41) * (1.0 - Rwall)**0.41)**-1.51
    p_mw = (3.84e-8 * (1.0 - Rwall)**0.62
            * R0 * a**1.38 * kappa**0.79
            * B**2.62 * ne0_20**0.38
            * Te * (16.0 + Te)**2.61
            * dum * g_function * k_function)
    return p_mw * 1e6


def p_sync_trubnikov(R0, a, kappa, B, ne, Te, Rwall=0.90):
    """Trubnikov/ITER-89 closed form via Zohm (2019) Eq. (6) [W]."""
    A = R0 / a
    V = 2.0 * math.pi**2 * R0 * a * a * kappa
    ne20 = ne * 1e-20
    p_mw = (1.32e-7 * (B * Te)**2.5 * math.sqrt(A * ne20 / R0)
            * (1.0 + 18.0 / (A * math.sqrt(Te))) * V)
    return p_mw * 1e6 * math.sqrt(max(1.0 - Rwall, 0.0) / (1.0 - ZOHM_RWALL))


def p_sync_optically_thin(R0, a, kappa, B, ne, Te):
    """Optically thin cyclotron hard upper bound [W]."""
    from scipy.integrate import quad
    theta = Te / MEC2_KEV
    num = quad(lambda p: p**4 * np.exp(-(np.sqrt(1 + p * p) - 1) / theta), 0, 60,
               limit=400, epsabs=1e-300, epsrel=1e-12)[0]
    den = quad(lambda p: p**2 * np.exp(-(np.sqrt(1 + p * p) - 1) / theta), 0, 60,
               limit=400, epsabs=1e-300, epsrel=1e-12)[0]
    p2 = num / den
    U_B = B * B / (2.0 * MU0)
    V = math.pi * a * a * (2.0 * math.pi * R0)
    return (4.0 / 3.0) * SIGMA_T * C_LIGHT * p2 * U_B * ne * V
