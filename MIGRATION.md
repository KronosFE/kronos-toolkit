# Migrating to the Kronos Toolkit

You don't need to rewrite all ~950 scripts. New work imports the toolkit; hot-path
old work migrates when it's touched. This maps the highest-traffic legacy engines to
their toolkit calls and gives drop-in shims.

## Engine map

| legacy script | legacy call | toolkit call |
|---|---|---|
| `KRONOS_PAPERS_2026-07-31/code_and_env/dt_evaluator.py` | `evaluate(fuel, R0, A, ...)` | `kronos_toolkit.core.evaluate_breeder(fuel, R0, A, ..., f_he4=0.05)` |
| `KRONOS_PAPERS_2026-07-31/code_and_env/kronos_clean.py` | `sigmav`, `p_brems`, `p_sync`, `tau_E_IPB98y2`, `sauter_bootstrap` | `kronos_toolkit.core.reactivities` / `.radiation` / `.confinement` |
| `2026 August Publication Research/mode_k/mirror.py` | `solve_point(ne, x_he3, Ti_keV, ...)` | `kronos_toolkit.core.solve_mirror(ne, x_he3, Ti_keV, ...)` |
| `2026 August Publication Research/mode_k/kronos_ledger.py` | plant electrical ledger | `kronos_toolkit.core.solve_mirror(...)` outputs + `report.Study` |
| `PHASE 3 .../HYPERION/UPSIDE/exporter_push.py` | surplus law | `kronos_toolkit.core.surplus_kg_per_fpy(net_tbr)` |
| `.../BC-B stress-test/scripts/bc_b_stress_test.py` | coil stress | `kronos_toolkit.hifi.ADAPTERS["struct_fea"].run(B_T=...)` |
| assorted `*_openmc*.py` | OpenMC TBR/fluence | `kronos_toolkit.neutronics.tbr(...)` / `.coil_fluence(...)` |
| assorted UQ (`R2*`, `J3*`) | Monte-Carlo / Sobol | `kronos_toolkit.uq.mc_sample` / `.sobol_indices` / `.tornado_chart` |

## Key detail: the breeder ash fraction

Config 22021 in `dt_scan.csv` was generated with an **undeclared 5% helium-ash
fraction** (`f_he4=0.05`). Reproducing the frozen anchors requires it:

```python
from kronos_toolkit.core import evaluate_breeder
r = evaluate_breeder(fuel="DT", R0=1.2, A=2.5, kappa=2.0, B0=8.0, q95=3.0,
                     fG=0.3, Ti0=15.0, TBR_dt=1.8, f_he4=0.05)
assert abs(r["Q"] - 3.423913) < 1e-4     # matches the frozen record
```

## Drop-in shims

Point a legacy import at the toolkit without changing call sites.

**Breeder** — replace `import dt_evaluator` usage:

```python
# legacy: row = dt_evaluator.evaluate(fuel, R0, A, kappa, B0, q95, fG, Ti0, TBR_dt)
from kronos_toolkit.core import evaluate_breeder as _evb
def evaluate(*a, **k):
    k.setdefault("f_he4", 0.05)     # the config-22021 convention
    return _evb(*a, **k)
```

**Mirror** — replace `from mirror import solve_point`:

```python
from kronos_toolkit.core import solve_mirror as solve_point
# same kwargs: ne, x_he3, Ti_keV, a_c, l_c, beta_c, B_m, n_plug_over_n_c
```

**Surplus law** — replace the inline `(net_tbr - 1) * T_burn`:

```python
from kronos_toolkit.core import surplus_kg_per_fpy
kg = surplus_kg_per_fpy(net_tbr)     # T_burn handled internally (4.97 kg-T/fpy)
```

## Recommended pattern for new studies

Copy a file from `study_template/` and follow the scaffold:

```python
from kronos_toolkit.report import Study
s = Study("my_scan", out_dir="results", public=True)
s.pre_register(question=..., hypothesis=..., method=..., gate=...)
s.run(evaluate_breeder, cases, columns=["Q", "P_fus_MW"])
s.to_csv(); s.manifest(); s.verdict("NO-GO", "net power not reached")
```

You get a CSV, a two-tier reproducibility manifest (byte hash + tolerances), a
recorded verdict against the pre-registered gate, and — for public studies — the
no-economics firewall, for free. Rebuild the dashboard over your results with
`kronos-viz build --results results`.

## Verifying a migration

After porting a hot-path script, confirm it still matches canon:

```
python -m kronos_toolkit.verify.regression      # 19/19 must pass
```

If your script fed the digital twin, also run the twin's bridge test
(`.../3D_Model .../solver/_toolkit_anchor_bridge.py`) — it asserts the twin's solver
still equals the toolkit.
