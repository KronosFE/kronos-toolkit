"""Assemble the dashboard data model from live toolkit state — single source of truth.

Everything here is read from the frozen anchors, the engines, and (optionally) a
results directory of study CSVs/manifests. Nothing is hardcoded that the toolkit
already owns, so the dashboard is always current with the physics.
"""
import os
import csv
import glob
import json
from .. import __version__, SEED
from .gates import compute_gates


def design_points():
    """Breeder + burner design-point cards, numbers pulled from the live engines."""
    from ..core.breeder import evaluate_breeder
    from ..core.mirror_balance import solve_mirror
    from ..verify.anchors import BREEDER_DP, BURNER_DP

    br = evaluate_breeder(**BREEDER_DP)
    bu = solve_mirror(**BURNER_DP)

    breeder = dict(
        name="Hyperion (breeder)", mode="D-T spherical tokamak",
        metrics=[
            ("Q_sci", f"{br['Q']:.3f}"),
            ("P_fus", f"{br['P_fus_MW']:.1f} MW"),
            ("I_p", f"{br['Ip_MA']:.2f} MA"),
            ("T surplus law", f"{br['T_kg_yr']:.2f} kg-T/fpy burn"),
            ("neutron fraction", f"{br['f_n']*100:.1f}%"),
        ],
        honest="Scientific gain, not net electric. Supported platform (isotopes/materials).",
    )
    burner = dict(
        name="Aegis / MetroVolt (burner)", mode="D-3He axisymmetric HTS tandem mirror",
        metrics=[
            ("Q_E", f"{bu['Q_E']:.3f}"),
            ("P_fus", f"{bu['P_fus_MW']:.0f} MW"),
            ("P_n", f"{bu['P_n_MW']:.1f} MW"),
            ("neutron fraction", f"{bu['f_n']*100:.2f}%"),
            ("phi_i", f"{bu['phi_i_keV']:.1f} keV"),
        ],
        honest="Q_E>1 only with plug density n_plug/n_c=16 (a requirement, not yet shown).",
    )
    return [breeder, burner]


def extrapolation_ledger():
    """Reach-vs-demonstrated per parameter (the Hammer/Dongarra honesty view)."""
    return [
        dict(parameter="Breeder net TBR", demonstrated="0.74 (3-D, net)",
             reach="1.0+ (self-sufficient)", gap="blanket closure"),
        dict(parameter="Burner Q_E", demonstrated="<1 net today",
             reach="1.32 at M-45 with plug", gap="plug-density requirement"),
        dict(parameter="Plug density n_plug/n_c", demonstrated="not shown",
             reach="16x required", gap="magnetic well at feasible beta"),
        dict(parameter="Coil peak-fiber factor", demonstrated="0.26x vs 0.785x",
             reach="single adjudicated value", gap="real structural FEA"),
        dict(parameter="Synchrotron closure", demonstrated="AFJ vs Trubnikov",
             reach="single transported value", gap="SPECE/CYNEQ transport"),
        dict(parameter="He-3 supply", demonstrated="none terrestrial",
             reach="lunar ~2038-40", gap="lunar mining flywheel"),
    ]


def paper_tracker():
    """Live DOI/closure tracker for the deposited papers."""
    return [
        dict(paper="Breeder (Hyperion)", doi="10.5281/zenodo.21746157", closure="platform, not net power"),
        dict(paper="Breeder v2", doi="10.5281/zenodo.21795620", closure="platform, not net power"),
        dict(paper="Burner (Aegis/MetroVolt)", doi="10.5281/zenodo.21746479", closure="plug-gated"),
        dict(paper="REBCO magnet", doi="10.5281/zenodo.21842514", closure="FEA contradiction open"),
        dict(paper="DEC (D-3He tandem)", doi="10.5281/zenodo.21842864", closure="conversion chain"),
        dict(paper="AI + Quantum", doi="10.5281/zenodo.21842371", closure="methods deposit"),
    ]


def load_studies(results_dir):
    """Scan a results directory for study manifests + CSVs. Returns a list."""
    studies = []
    if not results_dir or not os.path.isdir(results_dir):
        return studies
    for man_path in sorted(glob.glob(os.path.join(results_dir, "**", "*.manifest.json"),
                                     recursive=True)):
        try:
            with open(man_path) as f:
                man = json.load(f)
        except Exception:
            continue
        rows = []
        csv_path = man_path.replace(".manifest.json", ".csv")
        if os.path.exists(csv_path):
            with open(csv_path) as f:
                rows = list(csv.DictReader(f))
        studies.append(dict(
            name=man.get("study"),
            verdict=man.get("verdict"),
            registration=man.get("registration"),
            columns=man.get("columns", []),
            n_rows=man.get("n_rows", len(rows)),
            byte_hash=man.get("tier1_byte_hash", "")[:12],
            rows=rows[:50],
        ))
    return studies


def build_model(results_dir=None, public=True):
    """Assemble the full dashboard model. Public mode is firewall-guarded by caller."""
    return dict(
        toolkit_version=__version__,
        seed=SEED,
        mode="public" if public else "confidential",
        design_points=design_points(),
        gates=compute_gates(),
        extrapolation=extrapolation_ledger(),
        papers=paper_tracker(),
        studies=load_studies(results_dir),
    )
