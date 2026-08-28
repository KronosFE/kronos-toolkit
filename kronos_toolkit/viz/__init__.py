"""kronos_toolkit.viz — the visual research layer (lives on the data).

A self-contained HTML dashboard read directly from the frozen anchors, the
engines, and any study results — so it is always current. Two modes: public
(firewall-clean, no economics) and confidential (internal). Rebuild with the
`kronos-viz build` command or `build_dashboard(...)`.
"""
from .build import build_dashboard
from .data import build_model
from .gates import compute_gates
