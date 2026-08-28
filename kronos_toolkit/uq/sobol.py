"""Sobol variance-based sensitivity via the Saltelli estimator.

Self-contained: no SALib dependency. First- and total-order indices.
Deterministic under the shared seed.
"""
import numpy as np
from .. import SEED


def _saltelli_matrices(rng, n_base, bounds):
    d = len(bounds)
    A = rng.random((n_base, d))
    B = rng.random((n_base, d))
    for j, (lo, hi) in enumerate(bounds):
        A[:, j] = lo + A[:, j] * (hi - lo)
        B[:, j] = lo + B[:, j] * (hi - lo)
    AB = []
    for i in range(d):
        ABi = A.copy()
        ABi[:, i] = B[:, i]
        AB.append(ABi)
    return A, B, AB


def sobol_indices(evaluator, params, distributions, output_key,
                  n_base=1024, seed=SEED):
    """First- and total-order Sobol indices via Saltelli sampling.

    Parameters
    ----------
    evaluator : callable
        Function(**params) -> dict of outputs.
    params : dict
        Baseline parameter values (non-varied held fixed).
    distributions : dict
        {param_name: (lo, hi)} uniform ranges for varied parameters.
    output_key : str
        Output to analyze.
    n_base : int
        Base sample size. Total model runs = n_base * (d + 2).
    seed : int
        RNG seed.

    Returns
    -------
    dict with 'S1' (first-order), 'ST' (total-order), 'names', 'n_runs'.
    """
    rng = np.random.default_rng(seed)
    names = list(distributions.keys())
    bounds = [distributions[n] for n in names]
    d = len(names)

    A, B, AB = _saltelli_matrices(rng, n_base, bounds)

    def run_matrix(M):
        out = np.full(M.shape[0], np.nan)
        for i in range(M.shape[0]):
            kw = dict(params)
            for j, name in enumerate(names):
                kw[name] = float(M[i, j])
            try:
                out[i] = evaluator(**kw)[output_key]
            except Exception:
                out[i] = np.nan
        return out

    yA = run_matrix(A)
    yB = run_matrix(B)
    yAB = [run_matrix(ABi) for ABi in AB]

    # Mask rows where any of A/B failed
    mask = np.isfinite(yA) & np.isfinite(yB)
    for yABi in yAB:
        mask &= np.isfinite(yABi)
    yA_m, yB_m = yA[mask], yB[mask]
    var_y = np.var(np.concatenate([yA_m, yB_m]))

    S1, ST = {}, {}
    for i, name in enumerate(names):
        yABi = yAB[i][mask]
        if var_y <= 0:
            S1[name] = 0.0; ST[name] = 0.0
            continue
        # Jansen / Saltelli 2010 estimators
        s1 = np.mean(yB_m * (yABi - yA_m)) / var_y
        st = 0.5 * np.mean((yA_m - yABi) ** 2) / var_y
        S1[name] = float(s1)
        ST[name] = float(st)

    return dict(S1=S1, ST=ST, names=names, n_runs=n_base * (d + 2),
                var_output=float(var_y))
