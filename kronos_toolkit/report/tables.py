"""Paper-table export — markdown, LaTeX, CSV — from a list of row dicts.

Public exports are economics-guarded. Numbers format with a fixed precision so
tables are byte-reproducible across runs.
"""
from .guard import guard


def _fmt(v, prec=4):
    if isinstance(v, float):
        if v != v:            # NaN
            return "—"
        return f"{v:.{prec}g}"
    return "" if v is None else str(v)


def to_markdown(rows, columns, headers=None, prec=4, public=True):
    """Render rows as a GitHub-flavored markdown table."""
    if public:
        guard(rows, public=True, where="markdown table")
    heads = headers or columns
    out = ["| " + " | ".join(heads) + " |",
           "| " + " | ".join("---" for _ in heads) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(row.get(c), prec) for c in columns) + " |")
    return "\n".join(out)


def to_latex(rows, columns, headers=None, prec=4, caption="", label="", public=True):
    """Render rows as a LaTeX tabular (booktabs)."""
    if public:
        guard(rows, public=True, where="latex table")
    heads = headers or columns
    align = "l" + "r" * (len(columns) - 1)
    lines = [r"\begin{table}[htbp]", r"\centering",
             r"\begin{tabular}{" + align + "}", r"\toprule",
             " & ".join(heads) + r" \\", r"\midrule"]
    for row in rows:
        lines.append(" & ".join(_fmt(row.get(c), prec) for c in columns) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    if caption:
        lines.append(rf"\caption{{{caption}}}")
    if label:
        lines.append(rf"\label{{{label}}}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def write_table(rows, columns, path, fmt="md", public=True, **kw):
    """Write a table to disk in the requested format ('md' | 'tex')."""
    if fmt == "md":
        text = to_markdown(rows, columns, public=public, **kw)
    elif fmt in ("tex", "latex"):
        text = to_latex(rows, columns, public=public, **kw)
    else:
        raise ValueError("fmt must be 'md' or 'tex'")
    with open(path, "w") as f:
        f.write(text + "\n")
    return path
