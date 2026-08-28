"""The single neutronics API — OpenMC when present, analytic otherwise.

Each function returns a Tagged result: [D] if OpenMC answered, [T] (retired_by
OpenMC) if the analytic surrogate did. `force_analytic=True` pins the surrogate
for reproducibility / CI.
"""
from ..verify.tags import derived, surrogate
from . import analytic

_OPENMC_RETIRES = "OpenMC (Monte-Carlo neutron transport)"


def openmc_available():
    """True if OpenMC can be imported in this environment."""
    try:
        import openmc  # noqa: F401
        return True
    except Exception:
        return False


def _use_openmc(force_analytic):
    return (not force_analytic) and openmc_available()


def tbr(li6_enrichment=0.90, blanket_thickness_m=0.80, multiplier="Be",
        coverage=0.92, force_analytic=False, **openmc_kwargs):
    """Tritium breeding ratio. Returns a Tagged dict (local_tbr, net_tbr, ...)."""
    if _use_openmc(force_analytic):
        # Real OpenMC path — only reached when a model builder is supplied.
        model = openmc_kwargs.get("model")
        if model is not None:
            from ._openmc import run_tbr_model
            return derived(run_tbr_model(model, **openmc_kwargs),
                           note="OpenMC tritium-production tally")
    res = analytic.tbr_analytic(li6_enrichment, blanket_thickness_m,
                                multiplier, coverage)
    return surrogate(res, retired_by=_OPENMC_RETIRES,
                     note="saturating blanket law, calibrated to frozen H1 anchor")


def coil_fluence(p_neutron_MW, shield_thickness_m, standoff_m=1.0,
                 full_power_years=1.0, force_analytic=False, **openmc_kwargs):
    """Fast-neutron fluence + dpa at the coil. Returns a Tagged dict."""
    if _use_openmc(force_analytic) and openmc_kwargs.get("model") is not None:
        from ._openmc import run_fluence_model
        return derived(run_fluence_model(**openmc_kwargs),
                       note="OpenMC fast-flux tally at coil surface")
    res = analytic.coil_fluence_analytic(
        p_neutron_MW, shield_thickness_m, standoff_m, full_power_years)
    return surrogate(res, retired_by=_OPENMC_RETIRES,
                     note="BANK1 exponential-attenuation fluence law")


def shielding_attenuation(thickness_m, lambda_atten_m=0.12, buildup=True,
                          force_analytic=False, **openmc_kwargs):
    """Dose attenuation through a shield. Returns a Tagged dict."""
    if _use_openmc(force_analytic) and openmc_kwargs.get("model") is not None:
        from ._openmc import run_shield_model
        return derived(run_shield_model(**openmc_kwargs),
                       note="OpenMC dose tally through shield")
    res = analytic.shielding_attenuation_analytic(
        thickness_m, lambda_atten_m, buildup)
    return surrogate(res, retired_by=_OPENMC_RETIRES,
                     note="exponential + linear-buildup attenuation")


def penetration_streaming(duct_length_m, duct_radius_m, n_legs=1,
                          wall_albedo=0.05, force_analytic=False, **openmc_kwargs):
    """Duct streaming attenuation. Returns a Tagged dict."""
    if _use_openmc(force_analytic) and openmc_kwargs.get("model") is not None:
        from ._openmc import run_streaming_model
        return derived(run_streaming_model(**openmc_kwargs),
                       note="OpenMC duct-streaming tally")
    res = analytic.penetration_streaming_analytic(
        duct_length_m, duct_radius_m, n_legs, wall_albedo)
    return surrogate(res, retired_by=_OPENMC_RETIRES,
                     note="Simon-Clifford duct-attenuation law")
