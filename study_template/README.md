# study_template

Copy-paste patterns for a Kronos study built on the toolkit. Each study follows the
same spine — **pre-register → run → CSV → manifest → verdict** — so results are
comparable and reproducible, and public studies pass the no-economics firewall.

## Files

- `_template.py` — a blank scaffold. Copy it, fill in the four pre-registration
  fields and your sweep, run it.
- `tritium_exporter_push.py` — worked example 1: scan → confirm → surplus. Uses
  `core` (surplus law) + `neutronics` (analytic/OpenMC TBR). Reproduces T_burn
  ≈ 4.97 kg-T/fpy and the net-TBR → surplus ladder.
- `coil_buildability.py` — worked example 2: coil peak-fiber stress vs the REBCO
  allowable across an on-coil field ladder. Uses `hifi.struct_fea` (the 0.785×
  surrogate, tagged `[T]`, retired by real FEA).

## Run

```
python study_template/tritium_exporter_push.py
python study_template/coil_buildability.py
```

Outputs land in `_results/<study_name>/` (CSV + manifest). Rebuild the dashboard
over them:

```
kronos-viz build --results study_template/_results --out dashboard.html
```

## The scaffold

```python
from kronos_toolkit.report import Study
from kronos_toolkit.core import evaluate_breeder

s = Study("my_study", out_dir="_results/my_study", public=True)
s.pre_register(
    question="...",              # the decision this study informs
    hypothesis="...",            # what you expect, before running
    method="...",                # engines + sweep
    gate="...",                  # the pass/fail line
)
cases = [dict(fuel="DT", R0=1.2, A=2.5, kappa=2.0, B0=b, q95=3.0, fG=0.3,
              Ti0=15.0, TBR_dt=1.8, f_he4=0.05) for b in (6.0, 7.0, 8.0)]
s.run(evaluate_breeder, cases, columns=["Q", "P_fus_MW", "Ip_MA"])
s.to_csv(); s.manifest()
s.verdict("CONDITIONAL", "…", evidence={...})
```

Public studies are economics-guarded automatically; if you genuinely need economics,
construct the study with `public=False` and keep it out of any public path.
