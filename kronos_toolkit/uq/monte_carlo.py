"""Monte-Carlo sampling over a physics evaluator.

Deterministic: seed 20260726 by default, reproducible across runs.
"""
import numpy as np
from .. import SEED


def mc_sample(evaluator, params, distributions, n_samples=2000, outputs=None,
              seed=SEED):
    """Run a Monte-Carlo ensemble over a physics evaluator.

    Parameters
    ----------
    evaluator : callable
        Function(**params) -> dict of outputs.
    params : dict
        Baseline parameter values.
    distributions : dict
        {param_name: (lo, hi)} for uniform or {param_name: (mu, sigma, 'normal')}
        for normal. Only listed params are varied.
    n_samples : int
        Number of samples.
    outputs : list[str] or None
        Output keys to collect. None = all scalar outputs from the first run.
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    dict with 'samples' (n_samples x n_outputs array), 'output_names', 'input_samples',
    'stats' (mean, std, p5, p95 per output).
    """
    rng = np.random.default_rng(seed)

    input_samples = {}
    for name, dist in distributions.items():
        if len(dist) == 3 and dist[2] == "normal":
            input_samples[name] = rng.normal(dist[0], dist[1], n_samples)
        else:
            input_samples[name] = rng.uniform(dist[0], dist[1], n_samples)

    results = []
    for i in range(n_samples):
        kw = dict(params)
        for name in distributions:
            kw[name] = float(input_samples[name][i])
        try:
            r = evaluator(**kw)
            results.append(r)
        except Exception:
            results.append(None)

    if outputs is None:
        ref = next((r for r in results if r is not None), None)
        if ref is None:
            return dict(samples=np.array([]), output_names=[], input_samples=input_samples,
                        stats={})
        outputs = [k for k, v in ref.items() if isinstance(v, (int, float)) and np.isfinite(v)]

    n_out = len(outputs)
    samples = np.full((n_samples, n_out), np.nan)
    for i, r in enumerate(results):
        if r is None:
            continue
        for j, key in enumerate(outputs):
            val = r.get(key, np.nan)
            if isinstance(val, (int, float)):
                samples[i, j] = val

    stats = {}
    for j, key in enumerate(outputs):
        col = samples[:, j]
        valid = col[np.isfinite(col)]
        if len(valid) > 0:
            stats[key] = dict(
                mean=float(np.mean(valid)),
                std=float(np.std(valid)),
                p5=float(np.percentile(valid, 5)),
                p95=float(np.percentile(valid, 95)),
                median=float(np.median(valid)),
                n_valid=len(valid),
            )
        else:
            stats[key] = dict(mean=np.nan, std=np.nan, p5=np.nan, p95=np.nan,
                              median=np.nan, n_valid=0)

    return dict(samples=samples, output_names=outputs,
                input_samples=input_samples, stats=stats)
