"""kronos_toolkit.hifi — the high-fidelity adapter layer (gap-fill spine).

Seven adapters, one contract: call the real code if it is installed ([D]),
otherwise a documented reduced-order surrogate ([T]) that names the real code
that retires it. Same interface either way.

    from kronos_toolkit.hifi import ADAPTERS
    res = ADAPTERS["struct_fea"].run(B_T=17.0)   # -> Tagged
    print(res.tag, res.value["peak_fiber_stress_MPa"])

Adapters: gyrokinetic, neoclassical, edge_sol, struct_fea, sync_transport,
kinetic_mirror, nucdata.
"""
from .base import Adapter
from .adapters import (
    ADAPTERS,
    Gyrokinetic, Neoclassical, EdgeSOL, StructFEA,
    SyncTransport, KineticMirror, NucData,
)


def run(adapter_name, force_surrogate=False, **kw):
    """Convenience: run one adapter by name. Returns a Tagged result."""
    if adapter_name not in ADAPTERS:
        raise KeyError(f"no adapter {adapter_name!r}; have {list(ADAPTERS)}")
    return ADAPTERS[adapter_name].run(force_surrogate=force_surrogate, **kw)


def status():
    """Report which adapters have their real code available in this environment."""
    return {name: ad.available() for name, ad in ADAPTERS.items()}
