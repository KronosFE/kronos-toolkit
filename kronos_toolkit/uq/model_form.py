"""Model-form uncertainty bands — spread across competing physics closures.

Where the physics admits more than one defensible model (e.g. synchrotron
radiation brackets, confinement scaling multipliers), evaluate each closure
and report the envelope. This is epistemic, not statistical: it is the honest
"we do not know which model is right" band, kept separate from Monte-Carlo.
"""
import numpy as np


def model_form_band(evaluator, params, closures, output_key):
    """Evaluate an output across competing model closures and return the envelope.

    Parameters
    ----------
    evaluator : callable
        Function(**params) -> dict of outputs.
    params : dict
        Baseline parameter values.
    closures : dict
        {closure_label: {param overrides}} — each entry swaps in a different
        model choice (e.g. {'AFJ': {'sync_model': 'afj'}, 'Trubnikov': {...}}).
    output_key : str
        Output to bracket.

    Returns
    -------
    dict with 'values' (per-closure output), 'low', 'high', 'span',
    'low_closure', 'high_closure', 'baseline'.
    """
    values = {}
    for label, overrides in closures.items():
        kw = dict(params); kw.update(overrides)
        try:
            values[label] = evaluator(**kw)[output_key]
        except Exception:
            values[label] = np.nan

    finite = {k: v for k, v in values.items() if np.isfinite(v)}
    if not finite:
        return dict(values=values, low=np.nan, high=np.nan, span=np.nan,
                    low_closure=None, high_closure=None, baseline=np.nan)

    low_closure = min(finite, key=finite.get)
    high_closure = max(finite, key=finite.get)
    low = finite[low_closure]
    high = finite[high_closure]

    return dict(
        values=values,
        low=low, high=high, span=high - low,
        low_closure=low_closure, high_closure=high_closure,
        baseline=float(np.median(list(finite.values()))),
    )
