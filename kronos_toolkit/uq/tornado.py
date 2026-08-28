"""Tornado sensitivity — one-at-a-time low/high swing per parameter, ranked by impact."""
import numpy as np


def tornado_chart(evaluator, params, ranges, output_key, baseline=None):
    """One-at-a-time sensitivity sweep.

    Parameters
    ----------
    evaluator : callable
        Function(**params) -> dict of outputs.
    params : dict
        Baseline parameter values.
    ranges : dict
        {param_name: (lo, hi)} range to swing each parameter across.
    output_key : str
        Which output to track.
    baseline : float or None
        Baseline output value. None = evaluate at params.

    Returns
    -------
    list of dicts sorted by descending swing magnitude, each with:
      param, lo_val, hi_val, low_output, high_output, swing, baseline.
    """
    if baseline is None:
        baseline = evaluator(**params)[output_key]

    rows = []
    for name, (lo, hi) in ranges.items():
        kw_lo = dict(params); kw_lo[name] = lo
        kw_hi = dict(params); kw_hi[name] = hi
        try:
            out_lo = evaluator(**kw_lo)[output_key]
        except Exception:
            out_lo = np.nan
        try:
            out_hi = evaluator(**kw_hi)[output_key]
        except Exception:
            out_hi = np.nan

        vals = [v for v in (out_lo, out_hi) if np.isfinite(v)]
        swing = (max(vals) - min(vals)) if len(vals) == 2 else np.nan
        rows.append(dict(
            param=name, lo_val=lo, hi_val=hi,
            low_output=out_lo, high_output=out_hi,
            swing=swing, baseline=baseline,
        ))

    rows.sort(key=lambda r: (-(r["swing"]) if np.isfinite(r["swing"]) else 1))
    return rows
