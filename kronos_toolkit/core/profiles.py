"""Profile shapes, geometry helpers, and volume-average utilities."""
import numpy as np
from .constants import MU0, RHO


def parab(rho, y0, ysep_frac, alpha):
    """Parabolic profile: y0 * ((1 - ysep_frac)*(1 - rho^2)^alpha + ysep_frac)."""
    return y0 * ((1 - ysep_frac) * (1 - rho**2)**alpha + ysep_frac)


def vol_avg(y, rho=RHO):
    """Volume average (cylindrical Jacobian: weight = rho)."""
    return float(np.trapezoid(np.asarray(y, float) * rho, rho)
                 / np.trapezoid(rho, rho))


def kappa_perim(kappa):
    """Elongated-perimeter correction: P_pol/(2 pi a) ~ sqrt((1+kappa^2)/2)."""
    return np.sqrt((1.0 + kappa**2) / 2.0)


def plasma_volume(R0, a, kappa):
    """Torus plasma volume [m^3]."""
    return 2 * np.pi * R0 * np.pi * a**2 * kappa


def n_greenwald_1e20(Ip_MA, a_m):
    """Greenwald density limit [1e20 m^-3]."""
    return Ip_MA / (np.pi * a_m**2)


def trapped_fraction(eps):
    """Neoclassical trapped particle fraction."""
    return 1.0 - (1.0 - eps)**2 / ((1.0 + 1.46 * np.sqrt(eps)) * np.sqrt(1.0 - eps**2))
