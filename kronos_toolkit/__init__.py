"""Kronos Research Toolkit — unified, versioned physics library."""
__version__ = "0.1.0"
SEED = 20260726

# numpy 2.0 renamed np.trapz -> np.trapezoid; the toolkit uses the 2.0 name. Shim so the engine
# also runs on numpy 1.x (the browser engine applies the same alias in kronos_engine.py).
import numpy as _np
if not hasattr(_np, "trapezoid"):
    _np.trapezoid = _np.trapz
