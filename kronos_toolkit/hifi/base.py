"""Uniform adapter base for the high-fidelity gap-fill layer.

Every gap between Kronos' 0-D engines and a real physics code gets ONE adapter
with the same shape:

    run(**kw)  -> Tagged result
                  [D] if the real code is on PATH / importable, else
                  [T] surrogate that names the real code that retires it.

    available() -> bool   (is the real code usable here?)
    surrogate(**kw) -> dict   (the documented reduced-order model)
    ANCHOR      -> frozen (input, output) pin so the surrogate can't drift.

This is the honest gap-fill contract: the same interface today (surrogate) and
the day the HPC/license/partnership lands (real code), and the caller always
learns which one answered.
"""
import shutil
import importlib
from ..verify.tags import derived, surrogate as _surrogate


class Adapter:
    name = "adapter"
    real_codes = ()          # candidate executables / importable modules
    retired_by = ""          # human-readable "real code that retires this"
    surrogate_note = ""      # one line describing the reduced-order model

    # --- availability ------------------------------------------------------
    def available(self):
        """True if any real code is on PATH (executable) or importable (module)."""
        for code in self.real_codes:
            if shutil.which(code):
                return True
            try:
                importlib.import_module(code)
                return True
            except Exception:
                pass
        return False

    # --- surrogate (subclass implements) ----------------------------------
    def surrogate(self, **kw):
        raise NotImplementedError

    def _real(self, **kw):
        # Subclasses override when a real-code path is wired. Default: no path.
        raise RuntimeError(
            f"{self.name}: real code path not wired in this environment")

    # --- the one entry point ----------------------------------------------
    def run(self, force_surrogate=False, **kw):
        if (not force_surrogate) and self.available():
            try:
                return derived(self._real(**kw),
                               note=f"{self.name}: real code")
            except Exception:
                pass  # fall through to surrogate rather than fabricate
        return _surrogate(self.surrogate(**kw),
                          retired_by=self.retired_by,
                          note=self.surrogate_note)
