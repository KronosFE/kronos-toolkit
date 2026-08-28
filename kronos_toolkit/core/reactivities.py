"""Fusion reactivities: Bosch-Hale parametric + stored PCHIP cross-section table.

The breeder engine uses Bosch-Hale directly (matching kronos_clean.py).
The mirror engine uses the stored table via PCHIP (matching mirror.py).
"""
import numpy as np
from scipy.interpolate import PchipInterpolator
from .constants import MEV_J

# ---------------------------------------------------------------- Bosch-Hale 1992
_BH = {
    "DDp": dict(BG=31.3970, mrc2=937814.0,
                C=[5.65718e-12, 3.41267e-3, 1.99167e-3, 0.0, 1.05060e-5, 0.0, 0.0],
                domain=(0.2, 100.0)),
    "DDn": dict(BG=31.3970, mrc2=937814.0,
                C=[5.43360e-12, 5.85778e-3, 7.68222e-3, 0.0, -2.96400e-6, 0.0, 0.0],
                domain=(0.2, 100.0)),
    "DT":  dict(BG=34.3827, mrc2=1124656.0,
                C=[1.17302e-9, 1.51361e-2, 7.51886e-2, 4.60643e-3, 1.35000e-2,
                   -1.06750e-4, 1.36600e-5],
                domain=(0.2, 100.0)),
    "D3He": dict(BG=68.7508, mrc2=1124656.0,
                 C=[5.51036e-10, 6.41918e-3, -2.02896e-3, -1.91080e-5, 1.35776e-4, 0.0, 0.0],
                 domain=(0.5, 190.0)),
}


def sigmav(rx, T_keV):
    """Bosch-Hale Maxwellian reactivity [m^3/s]. T_keV may be array."""
    p = _BH[rx]; C = p["C"]
    T = np.asarray(T_keV, dtype=float)
    lo, hi = p["domain"]
    Tc = np.clip(T, lo, hi)
    num = Tc * (C[1] + Tc * (C[3] + Tc * C[5]))
    den = 1.0 + Tc * (C[2] + Tc * (C[4] + Tc * C[6]))
    theta = Tc / (1.0 - num / den)
    xi = (p["BG"]**2 / (4.0 * theta))**(1.0 / 3.0)
    sv = C[0] * theta * np.sqrt(xi / (p["mrc2"] * Tc**3)) * np.exp(-3.0 * xi)
    return sv * 1e-6  # cm^3/s -> m^3/s


# ---------------------------------------------------------------- stored cross-section table
# Embedded from fuel_cross_sections.csv (Mode F EXFOR / Bosch-Hale 1992 pull).
# Used by the mirror engine for bit-exact reproduction.
_XS_TABLE = {
    "D-T (d,n)a": dict(
        Q_MeV=17.589,
        T_keV=[5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 70.0, 100.0, 123.0,
               150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 800.0, 1000.0],
        sv_m3s=[1.3657833184867878e-23, 1.1361654705836232e-22, 2.7399296107880726e-22,
                4.330201895538215e-22, 6.680782799096394e-22, 7.997634213159322e-22,
                8.64908494548689e-22, 8.938335428607232e-22, 8.447662458665835e-22,
                7.901694008760633e-22, 7.277355218059663e-22, 6.308451560972793e-22,
                5.576431716100012e-22, 5.021413370901903e-22, 4.592226039881319e-22,
                4.253176114221001e-22, 3.7560581883939404e-22, 3.4124398601258492e-22,
                2.973913321124823e-22, 2.7092791108719775e-22],
    ),
    "D-3He (d,p)a": dict(
        Q_MeV=18.353,
        T_keV=[5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 70.0, 100.0, 123.0,
               150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 800.0, 1000.0],
        sv_m3s=[6.376956401271051e-27, 2.1260732682232565e-25, 1.1753899893632573e-24,
                3.482112852415835e-24, 1.3627306472222094e-23, 3.1604475665803525e-23,
                5.553863949338884e-23, 1.0845273037148554e-22, 1.7184772663480242e-22,
                2.0491426774336144e-22, 2.3398841885708368e-22, 2.7589517827340805e-22,
                3.1144957865480263e-22, 3.435345801263577e-22, 3.7286335103300446e-22,
                3.99740699845615e-22, 4.470241624089124e-22, 4.869777272712643e-22,
                5.500226864313828e-22, 5.967864322353189e-22],
    ),
    "D-D (d,p)t": dict(
        Q_MeV=4.033,
        T_keV=[5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 70.0, 100.0, 123.0,
               150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 800.0, 1000.0],
        sv_m3s=[9.024114508305649e-26, 5.78126926016618e-25, 1.3899874638882316e-24,
                2.398954986744111e-24, 4.728252714517674e-24, 7.249152913041087e-24,
                9.83832561634108e-24, 1.5018233392647018e-23, 2.2439277486232552e-23,
                2.7628523411727436e-23, 3.298392590091824e-23, 4.049243358534039e-23,
                4.496798071912279e-23, 4.704324522987943e-23, 4.74979732502601e-23,
                4.698074809793381e-23, 4.465910299208628e-23, 4.19495345309092e-23,
                3.7271986127864975e-23, 3.383933487712089e-23],
    ),
    "D-D (d,n)3He": dict(
        Q_MeV=3.269,
        T_keV=[5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 70.0, 100.0, 123.0,
               150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 800.0, 1000.0],
        sv_m3s=[9.128065740555476e-26, 6.022654194861754e-25, 1.4810104425876351e-24,
                2.602651467423054e-24, 5.270589422797733e-24, 8.235123674769945e-24,
                1.1329787309647461e-23, 1.7610699723545596e-23, 2.681674196574574e-23,
                3.355376802490142e-23, 4.108864669669366e-23, 5.413911828350716e-23,
                6.639717217683516e-23, 7.833611669969107e-23, 9.0429127449052e-23,
                1.0317330712322772e-22, 1.3304509841043328e-22, 1.7510000823082048e-22,
                4.004015354158853e-22, 0.0],
    ),
}

# reaction label aliases (mirror.py convention)
R_DHE3 = "D-3He (d,p)a"
R_DDN  = "D-D (d,n)3He"
R_DDP  = "D-D (d,p)t"
R_DT   = "D-T (d,n)a"

# per-reaction product energetics [MeV]
PRODUCTS = {
    R_DHE3: dict(Q=18.353, charged=[(14.68, 1, 1.0), (3.67, 2, 4.0)], En=0.0),
    R_DDN:  dict(Q=3.269,  charged=[(0.82, 2, 3.0)],                  En=2.45),
    R_DDP:  dict(Q=4.033,  charged=[(3.02, 1, 1.0), (1.01, 1, 3.0)],  En=0.0),
    R_DT:   dict(Q=17.589, charged=[(3.52, 2, 4.0)],                  En=14.03),
}


def _build_pchip_table():
    """Build PCHIP interpolators from the stored table."""
    SV = {}
    for rxn, d in _XS_TABLE.items():
        T = np.array(d["T_keV"])
        sv = np.array(d["sv_m3s"])
        mask = sv > 0
        T_use, sv_use = T[mask], sv[mask]
        lp = PchipInterpolator(np.log(T_use), np.log(np.maximum(sv_use, 1e-40)))
        lo, hi = float(T_use.min()), float(T_use.max())
        def _make_fn(lp_=lp, lo_=lo, hi_=hi):
            def fn(T_keV):
                T_keV = np.asarray(T_keV, dtype=float)
                return np.where(
                    (T_keV >= lo_) & (T_keV <= hi_),
                    np.exp(lp_(np.log(np.clip(T_keV, lo_, hi_)))),
                    np.nan)
            return fn
        SV[rxn] = (_make_fn(), (lo, hi), d["Q_MeV"])
    return SV


SV_TABLE = _build_pchip_table()


def sigmav_table(reaction, T_keV):
    """Stored-table reactivity [m^3/s] via PCHIP interpolation."""
    fn, _, _ = SV_TABLE[reaction]
    return fn(T_keV)
