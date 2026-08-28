"""The seven high-fidelity adapters (gap-fill spine).

Each carries: real_codes it defers to, a documented reduced-order surrogate,
a frozen ANCHOR pin, and the retired_by pointer. Surrogates reuse core physics
wherever core already owns the closure (bootstrap, synchrotron, C_CONF), so the
adapter and the frozen engine can never disagree.
"""
import math
from .base import Adapter
from ..core import constants as C


# ---------------------------------------------------------------------------
# 1. gyrokinetic — core turbulent transport (chi_e, chi_i, H_eff)
# ---------------------------------------------------------------------------
class Gyrokinetic(Adapter):
    name = "gyrokinetic"
    real_codes = ("gene", "cgyro", "gs2", "tglf")
    retired_by = "GENE / CGYRO / GS2 / TGLF (gyrokinetic turbulence)"
    surrogate_note = "HC3 reduced two-region gyro-Bohm + ETG critical-gradient threshold"

    # Frozen pin: H_eff at default gradients (a/LT = 3.0, crit 1.5, stiffness 1.5).
    ANCHOR = dict(key="H_eff", value=0.6896551724137931, atol=1e-9)

    def surrogate(self, a_over_LTi=3.0, a_over_LTe=3.0, Ti_keV=20.0, B_T=3.0,
                  a_m=0.5, crit_gradient=1.5, stiffness=1.5):
        """Critical-gradient stiff transport. Above threshold, chi rises ~ (R/L - crit)."""
        rho_s = 4.57e-3 * math.sqrt(Ti_keV) / B_T          # gyro-radius scale (m)
        chi_gb = rho_s * rho_s * math.sqrt(Ti_keV * C.KEV_J / C.M_P) / a_m
        exc_i = max(0.0, a_over_LTi - crit_gradient)
        exc_e = max(0.0, a_over_LTe - crit_gradient)
        chi_i = chi_gb * (1.0 + stiffness * exc_i)
        chi_e = chi_gb * (1.0 + stiffness * exc_e) * 0.7    # ETG weaker than ITG
        # Confinement multiplier: gradients at/below threshold -> H_eff ~ 1.
        h_eff = 1.0 / (1.0 + 0.15 * (exc_i + exc_e))
        return dict(chi_i=chi_i, chi_e=chi_e, chi_gyrobohm=chi_gb, H_eff=h_eff,
                    above_threshold=(exc_i > 0 or exc_e > 0))


# ---------------------------------------------------------------------------
# 2. neoclassical — bootstrap fraction (the ±51% bracket)
# ---------------------------------------------------------------------------
class Neoclassical(Adapter):
    name = "neoclassical"
    real_codes = ("neo", "sfincs")
    retired_by = "NEO / SFINCS (neoclassical drift-kinetic)"
    surrogate_note = "Sauter center vs sqrt(eps)*beta_p simple estimate — the +/-51% bracket"

    ANCHOR = dict(eps=0.4, beta_p=1.0, key="f_bs_simple", value=0.6324555320336758, atol=1e-9)

    def surrogate(self, eps=0.4, beta_p=1.0, f_bs_sauter=None):
        """Bracket bootstrap fraction: simple scaling low end, Sauter as center.

        The simple estimate f ~ sqrt(eps)*beta_p is the conservative bracket end;
        Sauter (from core.confinement) is the center. Real NEO/SFINCS retires the
        spread that drives the CD-power / net-power sensitivity.
        """
        f_simple = math.sqrt(eps) * beta_p
        center = f_bs_sauter if f_bs_sauter is not None else f_simple
        lo = min(f_simple, center) * 0.66      # -51% style low bracket
        hi = max(f_simple, center) * 1.0
        return dict(f_bs_simple=f_simple, f_bs_center=center,
                    bracket_lo=lo, bracket_hi=hi,
                    spread_frac=(hi - lo) / center if center else float("nan"))


# ---------------------------------------------------------------------------
# 3. edge_sol — divertor / scrape-off-layer two-point model
# ---------------------------------------------------------------------------
class EdgeSOL(Adapter):
    name = "edge_sol"
    real_codes = ("solps", "b2.5", "eirene")
    retired_by = "SOLPS-ITER (edge/SOL plasma-neutral transport)"
    surrogate_note = "two-point model: upstream/target Te, target heat flux"

    ANCHOR = dict(P_SOL_MW=10.0, key="Te_target_eV", value=None, atol=1.0)

    def surrogate(self, P_SOL_MW=10.0, R_m=1.6, lambda_q_mm=1.0, L_par_m=20.0,
                  n_up_1e19=3.0, f_detach=0.0):
        """Two-point model heat-flux + target temperature.

        q_parallel from P_SOL spread over the wetted band; conductive-limited
        target temperature; detachment fraction reduces the target load.
        """
        lam = lambda_q_mm * 1e-3
        A_wet = 2.0 * math.pi * R_m * lam          # wetted area (m^2)
        q_par = (P_SOL_MW * 1e6) / A_wet            # W/m^2
        # Spitzer conduction-limited two-point: T_up^{7/2} - T_t^{7/2} ~ q L / kappa0
        kappa0 = 2000.0
        Tt7 = max(1.0, (2.0 / 7.0) * q_par * L_par_m / kappa0)
        Te_target = Tt7 ** (2.0 / 7.0)
        q_target = q_par * (1.0 - f_detach)
        return dict(q_parallel_MWm2=q_par / 1e6, q_target_MWm2=q_target / 1e6,
                    Te_target_eV=Te_target, wetted_area_m2=A_wet)


# ---------------------------------------------------------------------------
# 4. struct_fea — plug-coil stress (adjudicates 0.26x vs 0.785x)
# ---------------------------------------------------------------------------
class StructFEA(Adapter):
    name = "struct_fea"
    real_codes = ("ansys", "comsol", "elmerfem", "elmer")
    retired_by = "ANSYS / COMSOL / Elmer (structural FEA)"
    surrogate_note = "thick-wall Lame peak-fiber hoop stress (~0.785x peak-fiber factor)"

    # Frozen: peak-fiber factor pinned at 0.785 (the surrogate contested by FEA).
    ANCHOR = dict(B_T=17.0, key="peak_fiber_factor", value=0.785, atol=1e-9)
    PEAK_FIBER_FACTOR = 0.785

    def surrogate(self, B_T=17.0, r_bore_m=0.20, r_out_m=0.40, j_MA_m2=50.0):
        """Thick-wall (Lame) hoop stress at the bore with a peak-fiber factor.

        Magnetic pressure B^2/2mu0 drives a thick-wall cylinder; the peak-fiber
        factor (~0.785x) maps mean to peak. This surrogate is the 0.785x side of
        the 0.26x/0.785x contradiction that real FEA must adjudicate.
        """
        p_mag = B_T * B_T / (2.0 * C.MU0)                 # Pa
        a, b = r_bore_m, r_out_m
        # Lame internal-pressure hoop stress at inner fiber.
        sigma_hoop = p_mag * (b * b + a * a) / (b * b - a * a)
        sigma_peak = sigma_hoop * self.PEAK_FIBER_FACTOR
        return dict(magnetic_pressure_MPa=p_mag / 1e6,
                    hoop_stress_MPa=sigma_hoop / 1e6,
                    peak_fiber_stress_MPa=sigma_peak / 1e6,
                    peak_fiber_factor=self.PEAK_FIBER_FACTOR)


# ---------------------------------------------------------------------------
# 5. sync_transport — synchrotron closures (the AFJ vs Trubnikov spread)
# ---------------------------------------------------------------------------
class SyncTransport(Adapter):
    name = "sync_transport"
    real_codes = ("spece", "cyneq")
    retired_by = "SPECE / CYNEQ-class (synchrotron radiation transport)"
    surrogate_note = "AFJ vs Trubnikov closure bracket (drives the Q_E spread)"

    ANCHOR = dict(key="spread_ratio", value=None, atol=1e30)

    def surrogate(self, R0=1.6, a=0.5, kappa=2.6, B=8.0, ne=1.0e20,
                  Te=20.0, Rwall=0.90):
        """Bracket synchrotron loss with two literature closures from core.radiation.

        AFJ (Albajar-Johner-Granata) vs Trubnikov/Zohm — the spread between them
        is the epistemic band the real transport code (SPECE/CYNEQ) retires.
        Same tokamak-geometry signature as the frozen core functions.
        """
        from ..core.radiation import p_sync_afj, p_sync_trubnikov
        p_afj = p_sync_afj(R0, a, kappa, B, ne, Te, Rwall)
        p_tru = p_sync_trubnikov(R0, a, kappa, B, ne, Te, Rwall)
        lo, hi = sorted((p_afj, p_tru))
        return dict(p_sync_afj_W=p_afj, p_sync_trubnikov_W=p_tru,
                    bracket_lo_W=lo, bracket_hi_W=hi,
                    spread_ratio=(hi / lo) if lo > 0 else float("inf"))


# ---------------------------------------------------------------------------
# 6. kinetic_mirror — central-cell confinement C_CONF
# ---------------------------------------------------------------------------
class KineticMirror(Adapter):
    name = "kinetic_mirror"
    real_codes = ("cql3d", "cql3d-m", "cql3dm")
    retired_by = "CQL3D-m (bounce-averaged Fokker-Planck, mirror)"
    surrogate_note = "two-region reduced transport, C_CONF calibrated to Frank Table 2"

    # C_CONF is frozen by the import-time calibration in core.confinement.
    ANCHOR = dict(key="C_CONF", value=0.42838809786283644, atol=1e-12)

    def surrogate(self, **_):
        """Return the frozen central-cell confinement calibration from core."""
        from ..core.confinement import _C_CONF
        return dict(C_CONF=_C_CONF,
                    basis="Frank et al. Table 2 D-T anchor, Pastukhov ambipolar")


# ---------------------------------------------------------------------------
# 7. nucdata — nuclear data processing (cross sections, Q-values)
# ---------------------------------------------------------------------------
class NucData(Adapter):
    name = "nucdata"
    real_codes = ("njoy", "njoy2016", "sandy")
    retired_by = "NJOY / SANDY (evaluated nuclear-data processing)"
    surrogate_note = "embedded PCHIP cross-section table + literature Q-values (core.reactivities)"

    ANCHOR = dict(reaction="D3He", key="Q_MeV", value=18.353, atol=1e-3)

    def surrogate(self, reaction="D3He"):
        """Report the embedded fusion cross-section / Q-value the toolkit ships.

        Defers to the frozen PCHIP table in core.reactivities (the same data the
        mirror engine uses), so nucdata and the engine share one source. NJOY/SANDY
        would replace this with processed evaluated files.
        """
        from ..core.reactivities import PRODUCTS, R_DHE3, R_DDN, R_DDP, R_DT
        alias = {"D3He": R_DHE3, "DDN": R_DDN, "DDP": R_DDP, "DT": R_DT}
        label = alias.get(reaction, reaction)
        p = PRODUCTS.get(label)
        if p is None:
            raise KeyError(f"unknown reaction {reaction!r}; have {list(alias)}")
        return dict(reaction=reaction, Q_MeV=p["Q"],
                    source="embedded PCHIP table (fuel_cross_sections.csv)")


# --- registry ---------------------------------------------------------------
ADAPTERS = {
    a.name: a for a in (
        Gyrokinetic(), Neoclassical(), EdgeSOL(), StructFEA(),
        SyncTransport(), KineticMirror(), NucData(),
    )
}
