"""OpenMC bridge — real transport, only imported when OpenMC is on the machine.

The public API (api.py) reaches this module only when `openmc_available()` is
True AND the caller supplies a `model` (an openmc.Model or a builder callable).
Kept deliberately thin: the toolkit owns the interface and the tally names; the
study owns the geometry/materials. We never fabricate a result — if the tally
is absent, we raise.
"""


def _as_model(model):
    import openmc
    if callable(model):
        model = model()
    if not isinstance(model, openmc.Model):
        raise TypeError("openmc path needs an openmc.Model or a callable returning one")
    return model


def _run(model):
    sp_path = model.run()
    import openmc
    return openmc.StatePoint(sp_path)


def run_tbr_model(model, tbr_tally="TBR", **_):
    sp = _run(_as_model(model))
    t = sp.get_tally(name=tbr_tally)
    local = float(t.mean.flatten()[0])
    return dict(local_tbr=local, net_tbr=local, engine="openmc")


def run_fluence_model(model, flux_tally="coil_fast_flux", **_):
    sp = _run(_as_model(model))
    t = sp.get_tally(name=flux_tally)
    return dict(fast_fluence_n_per_cm2=float(t.mean.flatten()[0]), engine="openmc")


def run_shield_model(model, dose_tally="shield_dose", **_):
    sp = _run(_as_model(model))
    t = sp.get_tally(name=dose_tally)
    return dict(attenuation_factor=float(t.mean.flatten()[0]), engine="openmc")


def run_streaming_model(model, streaming_tally="duct_exit", **_):
    sp = _run(_as_model(model))
    t = sp.get_tally(name=streaming_tally)
    return dict(streaming_factor=float(t.mean.flatten()[0]), engine="openmc")
