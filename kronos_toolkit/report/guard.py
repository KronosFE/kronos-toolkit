"""No-economics guard for public outputs.

The firewall in code: any study exporting to a PUBLIC path is scanned for
economic content. If a price, cost, valuation, or funding term appears in the
output, the guard raises rather than let it leak. Confidential/internal outputs
pass the flag `public=False` and are exempt.

This encodes the standing rule: no economics in any public-output path.
"""
import re

# Whole-word economic terms that must never appear in a public output.
_ECON_TERMS = [
    "cost", "costs", "price", "priced", "pricing", "capex", "opex",
    "lcoe", "revenue", "valuation", "funding", "npv", "irr", "payback",
    "ebitda", "wacc", "margin", "profit", "profitability", "dollar", "dollars",
    "usd", "cash", "financing", "loan", "debt", "equity", "raise",
    "offtake price", "levelized", "amortization", "discount rate",
]
_ECON_RE = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(t) for t in _ECON_TERMS) + r")(?![a-z])",
    re.IGNORECASE)
# Currency symbols / money patterns.
_MONEY_RE = re.compile(r"[$€£]\s?\d|\d+\s?(?:M|B|bn|mn)\b|/kWh|per\s?kWh", re.IGNORECASE)


class EconomicsLeak(Exception):
    """Raised when economic content is found in a public output."""


def _scan_text(text):
    hits = set()
    for m in _ECON_RE.finditer(text):
        hits.add(m.group(1).lower())
    if _MONEY_RE.search(text):
        hits.add("<money-pattern>")
    return hits


def scan(obj):
    """Return the set of economic terms found anywhere in obj (keys + values)."""
    hits = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                hits.update(_scan_text(str(k)))
                walk(v)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                walk(v)
        else:
            hits.update(_scan_text(str(o)))

    walk(obj)
    return hits


def assert_public_clean(obj, where="output"):
    """Raise EconomicsLeak if obj carries economic content. No-op if clean."""
    hits = scan(obj)
    if hits:
        raise EconomicsLeak(
            f"economic content in public {where}: {sorted(hits)}. "
            "Mark this output public=False (confidential) or strip the economics.")
    return True


def guard(obj, public=True, where="output"):
    """Guard an output. public=True enforces the firewall; public=False exempts."""
    if public:
        assert_public_clean(obj, where=where)
    return obj
