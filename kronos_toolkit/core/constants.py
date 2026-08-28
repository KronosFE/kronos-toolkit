"""Physical constants and program-wide settings. SI units unless name says otherwise."""
import math
import numpy as np

SEED = 20260726

# fundamental
E_CHG   = 1.602176634e-19       # C
EPS0    = 8.8541878128e-12      # F/m
H_PL    = 6.62607015e-34        # J s
M_E     = 9.1093837015e-31      # kg
M_P     = 1.67262192369e-27     # kg
C_LIGHT = 2.99792458e8          # m/s
K_B     = 1.380649e-23          # J/K
MU0     = 4e-7 * math.pi        # H/m

# derived energy conversions
MEC2_KEV = M_E * C_LIGHT**2 / (E_CHG * 1e3)   # 511.0 keV
MEV_J    = 1.602176634e-13      # J per MeV
KEV_J    = 1.602176634e-16      # J per keV
QE       = E_CHG                 # alias used in mirror code

# time / mass
YEAR_S   = 3.15576e7            # s (Julian year)
FPY_S    = YEAR_S               # alias: full-power-year = Julian year
M_T_KG   = 3.01604928 * 1.66053906660e-27   # kg per triton
M_HE3_KG = 3.01602932 * 1.66053906660e-27   # kg per He-3

# reaction energetics [MeV] — ENDF/B-VIII.0 Q-values
E_DDP  = 4.03    # D(d,p)T total Q
E_DDN  = 3.27    # D(d,n)He3 total Q
E_DT   = 17.59   # T(d,n)He4 total Q
E_D3HE = 18.35   # He3(d,p)He4 total Q
EN_DDN = 2.45    # neutron-carried share, D-D(n)
EN_DT  = 14.03   # neutron-carried share, D-T

# Thomson cross-section
SIGMA_T = 6.6524587321e-29  # m^2

# breeder-specific switches (dt_evaluator defaults)
SYNC_CAL      = 6.51
BETAN_NOWALL  = 4.2
BETAN_RWM     = 5.5
B_COIL_DEMO   = 20.1
INBOARD_BUILD = 0.15
DPA_PER_MWYR  = 10.0
DUTY_LO       = 1.87
DUTY_HI       = 4.0

# mirror-specific
ETA_TH  = 0.45
ETA_WP  = 0.45
ETA_DEC = 0.70
BREMS_PREF_CLASSIC = 5.35e-37
ZOHM_RWALL = 0.80

# standard radial grid
RHO = np.linspace(1e-3, 1.0, 161)
