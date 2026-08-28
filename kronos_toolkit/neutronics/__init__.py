"""kronos_toolkit.neutronics — TBR, coil fluence, shielding, streaming.

One API. Uses OpenMC when it is importable (tagged [D]); otherwise falls back
to the documented analytic model (tagged [T]) that names OpenMC as the code
that retires it. The caller sees the same interface either way and always
learns which engine answered.
"""
from .api import (
    tbr,
    coil_fluence,
    shielding_attenuation,
    penetration_streaming,
    openmc_available,
)
