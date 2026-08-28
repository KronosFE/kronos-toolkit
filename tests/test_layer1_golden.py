"""Layer-1 golden regression tests — local compute node.

Pins the established Layer-1 results so any drift in the toolkit or its
dependencies is caught by re-running pytest. Golden reference:
_HPC_CAMPAIGN_RESULTS_2026-08-25/he3_fuelcycle/results.json.
"""
import json
import math
from pathlib import Path

import pytest

GOLDEN = (
    Path(__file__).resolve().parents[2]
    / "01 - Research and Data"
    / "PHASE 3 - Detailed Design Papers"
    / "_HPC_CAMPAIGN_RESULTS_2026-08-25"
    / "he3_fuelcycle"
    / "results.json"
)


@pytest.fixture(scope="module")
def golden():
    if not GOLDEN.exists():
        pytest.skip(f"golden reference not found: {GOLDEN}")
    return json.loads(GOLDEN.read_text())


def test_tritium_decay_constants_first_principles(golden):
    """lambda and mean life must follow from t_half = 12.32 yr exactly."""
    c = golden["constants"]
    t_half = c["t_half_yr"]
    assert t_half == pytest.approx(12.32, abs=1e-9)
    assert c["lambda_T_per_yr"] == pytest.approx(math.log(2) / t_half, rel=1e-12)
    assert c["mean_life_yr"] == pytest.approx(t_half / math.log(2), rel=1e-12)


def test_specific_burn_rate_consistency(golden):
    """T burn rate ~0.056 kg per MW-fpy is the D-T mass-burn invariant."""
    c = golden["constants"]
    assert c["T_specific_burn_kg_per_MW_fpy"] == pytest.approx(0.056, rel=1e-3)


def test_breeder_design_point_snapshot(golden):
    """Snapshot-pin the breeder anchor numbers used across the register."""
    b = golden["breeder"]
    assert b["P_fus_MW"] == pytest.approx(85.0)
    assert b["TBR"] == pytest.approx(1.15, rel=1e-6)
    # burn rate must equal P_fus * specific burn
    c = golden["constants"]
    assert b["T_burn_kg_fpy"] == pytest.approx(
        b["P_fus_MW"] * c["T_specific_burn_kg_per_MW_fpy"], rel=1e-2
    )


def test_d3he_energetics(golden):
    """D-3He reaction energy 18.35 MeV and charged-particle fraction."""
    c = golden["constants"]
    assert c["E_d3he_MeV"] == pytest.approx(18.35, abs=1e-6)
    assert 0.9 < c["frac_power_d3he"] <= 1.0
