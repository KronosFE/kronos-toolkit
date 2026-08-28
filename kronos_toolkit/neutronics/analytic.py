"""Analytic neutronics fallbacks — the reduced-order models.

These are the [T] surrogates: closed-form estimates good enough to scope a
study when OpenMC is not on the machine. Each names OpenMC as the code that
retires it. Never present these as transport-grade results.
"""
import math

# Frozen breeder reference: local TBR 1.1517 at the config-22021 blanket
# (H1 anchor), net TBR 0.7424 after penetrations/structure. Used to calibrate
# the analytic blanket law so the surrogate reproduces the frozen record.
TBR_LOCAL_ANCHOR = 1.1517
TBR_NET_ANCHOR = 0.7424
_PENETRATION_DERATE = TBR_NET_ANCHOR / TBR_LOCAL_ANCHOR   # 0.6446...


def tbr_analytic(li6_enrichment=0.90, blanket_thickness_m=0.80,
                 multiplier="Be", coverage=0.92, penetration_derate=None):
    """Reduced-order tritium breeding ratio.

    A saturating blanket law calibrated to the frozen local-TBR anchor (1.1517)
    at the reference enrichment/thickness, then scaled by coverage and a
    penetration derate to a *net* TBR. Not a transport calc — a scoping law.

    Returns dict: local_tbr, net_tbr, plus the inputs echoed.
    """
    mult_gain = {"Be": 1.0, "Pb": 1.06, "none": 0.82}.get(multiplier, 1.0)

    # Saturating in thickness (mean free path ~0.35 m), rising with Li-6.
    thick_factor = 1.0 - math.exp(-blanket_thickness_m / 0.35)
    thick_ref = 1.0 - math.exp(-0.80 / 0.35)
    enr_factor = 0.55 + 0.45 * (li6_enrichment / 0.90)

    # Calibrate so defaults reproduce the frozen local anchor exactly.
    base = TBR_LOCAL_ANCHOR / (thick_ref * (0.55 + 0.45) * 1.0)
    local = base * thick_factor * enr_factor * mult_gain

    derate = _PENETRATION_DERATE if penetration_derate is None else penetration_derate
    net = local * coverage / 0.92 * derate

    return dict(
        local_tbr=local, net_tbr=net,
        li6_enrichment=li6_enrichment, blanket_thickness_m=blanket_thickness_m,
        multiplier=multiplier, coverage=coverage,
        penetration_derate=derate,
    )


def coil_fluence_analytic(p_neutron_MW, shield_thickness_m, standoff_m=1.0,
                          full_power_years=1.0, lambda_atten_m=0.12):
    """BANK1-style fast-neutron fluence at the coil after a shield.

    Uncollided-plus-buildup exponential attenuation through the shield, geometric
    1/r^2 from an equivalent point source, integrated over full-power years.
    Returns dict: fast_fluence_n_per_cm2, dpa_estimate, atten_factor.
    """
    # Source fast-neutron rate: ~ P_n / E_n, E_n ~ 14.06 MeV for D-T.
    E_n_J = 14.06e6 * 1.602176634e-19
    s_rate = (p_neutron_MW * 1e6) / E_n_J           # neutrons/s (whole device)

    atten = math.exp(-shield_thickness_m / lambda_atten_m)
    geom = 1.0 / (4.0 * math.pi * (standoff_m * 100.0) ** 2)   # per cm^2 at standoff
    seconds = full_power_years * 3.15576e7

    fast_fluence = s_rate * atten * geom * seconds
    # Rough Fe/REBCO dpa cross-section proxy: ~1e-21 dpa per (n/cm^2) fast.
    dpa = fast_fluence * 1.0e-21

    return dict(
        fast_fluence_n_per_cm2=fast_fluence,
        dpa_estimate=dpa,
        atten_factor=atten,
        lambda_atten_m=lambda_atten_m,
        shield_thickness_m=shield_thickness_m,
    )


def shielding_attenuation_analytic(thickness_m, lambda_atten_m=0.12,
                                   buildup=True):
    """Exponential dose attenuation through a homogeneous shield.

    Returns dict: attenuation_factor, tenth_value_layers, lambda_atten_m.
    With buildup, a linear Taylor buildup factor B = 1 + mu*x softens the pure
    exponential (conservative for deep shields).
    """
    mu = 1.0 / lambda_atten_m
    x = thickness_m
    b = (1.0 + mu * x) if buildup else 1.0
    atten = b * math.exp(-mu * x)
    tvl = thickness_m / (lambda_atten_m * math.log(10.0))
    return dict(
        attenuation_factor=atten,
        tenth_value_layers=tvl,
        lambda_atten_m=lambda_atten_m,
        buildup=buildup,
    )


def penetration_streaming_analytic(duct_length_m, duct_radius_m,
                                   n_legs=1, wall_albedo=0.05):
    """Simon-Clifford straight/dog-leg duct streaming attenuation.

    Line-of-sight solid-angle term plus wall-scatter albedo contribution,
    reduced per dog-leg. Returns dict: streaming_factor (fraction of entrance
    dose reaching the exit), los_factor, scatter_factor.
    """
    a = duct_radius_m
    L = duct_length_m
    # Line-of-sight: solid angle of exit seen from entrance ~ a^2 / (4 L^2).
    los = (a * a) / (4.0 * L * L) if L > 0 else 1.0
    # Wall-scattered contribution (Simon-Clifford albedo term).
    scatter = wall_albedo * (2.0 * a / L) if L > 0 else wall_albedo
    factor = los + scatter
    # Each additional leg (dog-leg) suppresses line-of-sight strongly.
    factor = factor * (0.1 ** (n_legs - 1))
    return dict(
        streaming_factor=factor,
        los_factor=los,
        scatter_factor=scatter,
        n_legs=n_legs,
    )
