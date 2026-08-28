# Kronos Research Toolkit

**One versioned, anchor-tested Python engine behind the Kronos breeder and burner
designs** — replacing ~950 one-off scripts that each re-derived the same physics.

Every headline number Kronos publishes can be reproduced by running this library.
Where the toolkit stands in for a high-fidelity code it has not run, it says so
honestly: that result is tagged `[T]` and names the real code that would retire it.

```
from kronos_toolkit.core import evaluate_breeder, solve_mirror, surplus_kg_per_fpy
from kronos_toolkit.verify import run_regression

run_regression()          # reproduces the frozen record, all anchors
```

## Why this exists

The research tree had grown ~950 loose `.py` files, each re-implementing the mirror
0-D power balance, the D-T breeder evaluator, TBR/neutronics, UQ, and the surplus
law. Fragile, un-versioned, inconsistent. This toolkit **unifies** those engines,
**verifies** them against a frozen anchor suite, and provides an **adapter layer**
so the real high-fidelity codes become plug-and-play the moment they are available.

It does **not** substitute high-fidelity physics. It makes the program cohesive and
honest about what is demonstrated versus what is reach.

## Install

```
pip install -e .            # core (numpy, scipy)
pip install -e .[plot]      # + matplotlib for report plotting
pip install -e .[neutronics]  # + OpenMC for real neutron transport
```

Python 3.9+. Deterministic throughout (seed `20260726`).

## Modules

| module | what it is |
|---|---|
| `core` | the frozen engines: D-T breeder evaluator, D-³He tandem-mirror power balance, reactivities (Bosch-Hale + embedded cross-section table), radiation, confinement, tritium surplus law |
| `verify` | the **frozen-anchor regression suite** + `[D]/[T]/[R]/[Q]` provenance tagging |
| `uq` | Monte-Carlo, tornado, Sobol/Saltelli, model-form bands — deterministic |
| `neutronics` | TBR, coil fluence, shielding, streaming — OpenMC if installed (`[D]`), analytic fallback otherwise (`[T]`), one API |
| `hifi` | the adapter spine: 7 adapters that call the real code if present, else a documented surrogate that names what retires it |
| `report` | study scaffold (pre-register → run → CSV → manifest → verdict), brand plotting, paper-table export, **no-economics firewall** |
| `viz` | the visual research layer — `kronos-viz build` regenerates a self-contained HTML dashboard from live data |

## The anchor guarantee

The toolkit is only trustworthy if it reproduces the frozen record exactly. The
regression suite pins every engine:

```
python -m kronos_toolkit.verify.regression
```

```
breeder.Q            3.423913   (dt_evaluator config 22021)
breeder.P_fus_MW    88.660424
burner.Q_E           1.318121   (mirror M-45 design point)
burner.P_fus_MW   4298.499304
surplus.1.80         3.979503   (net-TBR → kg-T/fpy)
neutronics.net_tbr   0.742400   (3-D blanket, H1 anchor)
...                             ALL PASS (19/19)
```

Any drift is a failure. The same anchors pin the digital-twin simulator's forked
solver (`.../3D_Model .../solver/_toolkit_anchor_bridge.py`) so the twin and the
canonical engine can never silently disagree.

## Honesty by construction

- **Surrogates are tagged.** A reduced-order stand-in returns a `[T]` value that
  *must* name the real code that retires it — e.g. the 0.785× peak-fiber coil-stress
  factor is `[T]`, retired by ANSYS/COMSOL/Elmer FEA.
- **Gates are honest.** The dashboard's gate board reports red/yellow/green from the
  live engines: breeder net electric power is NO-GO (Q is scientific gain, not net
  electric); tritium self-sufficiency is a deficit at the 3-D blanket (net TBR 0.74);
  the burner reaches Q_E>1 only with a plug-density requirement not yet demonstrated.
- **No economics in public outputs.** `report.guard` scans every public export and
  *refuses to emit* if a cost/price/valuation term appears. The `viz` dashboard runs
  the same firewall and defaults to the public view.

## Worked examples

Two reference studies in `study_template/` show the whole pipeline and double as
integration tests:

```
python study_template/tritium_exporter_push.py    # scan → confirm → surplus
python study_template/coil_buildability.py         # coil stress vs REBCO allowable
```

## The dashboard

```
kronos-viz build --out dashboard.html --results study_template/_results
kronos-viz build --confidential --out internal.html   # internal view
```

A single offline HTML file: gate board, design-point cards, extrapolation ledger
(reach vs demonstrated), the study results with reproducibility hashes, and the
paper/DOI tracker — all read live from the frozen anchors.

## Migrating existing scripts

See [`MIGRATION.md`](MIGRATION.md) — it maps the highest-traffic legacy scripts to
their toolkit calls and provides shims so hot-path work can switch over incrementally.

## License

Apache-2.0 (see [`LICENSE`](LICENSE)) — chosen over MIT for its explicit patent grant.
