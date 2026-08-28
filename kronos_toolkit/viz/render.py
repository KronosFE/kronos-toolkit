"""Render the dashboard model to a single self-contained HTML file.

Offline, portable, no server, no external assets. KFE brand: flat, paper ground,
no gradients / glows / teal. The full model is also embedded as JSON so the page
is machine-readable. Public mode is guarded upstream (build.py).
"""
import json
import html

# KFE palette (shared with report.plotting) — no teal, no neon.
INK = "#14171A"
PAPER = "#FBFAF7"
CARD = "#FFFFFF"
BREEDER = "#1F4E79"
BURNER = "#B5651D"
MUTED = "#8A8A82"
LINE = "#E3E1DA"
STATUS = {"green": "#2E7D46", "yellow": "#B08900", "red": "#A32D2D"}

_CSS = f"""
:root {{ --ink:{INK}; --paper:{PAPER}; --card:{CARD}; --muted:{MUTED}; --line:{LINE}; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height:1.5; }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px 64px; }}
h1 {{ font-size: 26px; font-weight: 600; margin: 0 0 2px; }}
h2 {{ font-size: 17px; font-weight: 600; margin: 34px 0 12px; padding-bottom:6px;
  border-bottom: 2px solid var(--ink); }}
.sub {{ color: var(--muted); font-size: 13px; margin-bottom: 4px; }}
.badge {{ display:inline-block; font-size:12px; padding:2px 9px; border-radius:999px;
  border:1px solid var(--line); color:var(--muted); }}
.grid {{ display:grid; gap:14px; }}
.cards {{ grid-template-columns: repeat(auto-fit, minmax(300px,1fr)); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
.card h3 {{ margin:0 0 2px; font-size:16px; font-weight:600; }}
.card .mode {{ color:var(--muted); font-size:12px; margin-bottom:10px; }}
.metric {{ display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px dotted var(--line); font-size:14px; }}
.metric span:last-child {{ font-variant-numeric: tabular-nums; font-weight:500; }}
.honest {{ margin-top:10px; font-size:12.5px; color:var(--muted); font-style:italic; }}
.gate {{ display:flex; align-items:flex-start; gap:12px; padding:11px 0; border-bottom:1px solid var(--line); }}
.dot {{ flex:0 0 auto; width:12px; height:12px; border-radius:50%; margin-top:5px; }}
.gate .g-name {{ font-weight:600; font-size:14.5px; }}
.gate .g-val {{ color:var(--muted); font-size:12px; margin-left:8px; font-variant-numeric:tabular-nums; }}
.gate .g-line {{ font-size:13px; color:#333; margin-top:2px; }}
.gate .g-src {{ font-size:11.5px; color:var(--muted); margin-top:3px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-weight:600; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.03em; }}
td.num {{ font-variant-numeric: tabular-nums; }}
.verdict {{ display:inline-block; font-size:11px; font-weight:600; padding:1px 8px; border-radius:6px; color:#fff; }}
a {{ color: {BREEDER}; }}
.foot {{ margin-top:40px; color:var(--muted); font-size:12px; }}
details {{ margin:8px 0; }} summary {{ cursor:pointer; font-size:13px; font-weight:500; }}
"""


def _esc(s):
    return html.escape(str(s), quote=True)


def _design_card(dp):
    metrics = "".join(
        f'<div class="metric"><span>{_esc(k)}</span><span>{_esc(v)}</span></div>'
        for k, v in dp["metrics"])
    return (f'<div class="card"><h3>{_esc(dp["name"])}</h3>'
            f'<div class="mode">{_esc(dp["mode"])}</div>{metrics}'
            f'<div class="honest">{_esc(dp["honest"])}</div></div>')


def _gate_row(g):
    color = STATUS.get(g["status"], MUTED)
    return (f'<div class="gate"><div class="dot" style="background:{color}"></div>'
            f'<div><div><span class="g-name">{_esc(g["name"])}</span>'
            f'<span class="g-val">{_esc(g.get("value",""))}</span></div>'
            f'<div class="g-line">{_esc(g["status_line"])}</div>'
            f'<div class="g-src">source: {_esc(g["source"])}</div></div></div>')


def _ledger_table(rows):
    head = "<tr><th>parameter</th><th>demonstrated</th><th>reach</th><th>gap to close</th></tr>"
    body = "".join(
        f'<tr><td>{_esc(r["parameter"])}</td><td>{_esc(r["demonstrated"])}</td>'
        f'<td>{_esc(r["reach"])}</td><td>{_esc(r["gap"])}</td></tr>' for r in rows)
    return f"<table>{head}{body}</table>"


def _papers_table(rows):
    head = "<tr><th>paper</th><th>DOI</th><th>honest closure</th></tr>"
    body = "".join(
        f'<tr><td>{_esc(r["paper"])}</td>'
        f'<td><a href="https://doi.org/{_esc(r["doi"])}">{_esc(r["doi"])}</a></td>'
        f'<td>{_esc(r["closure"])}</td></tr>' for r in rows)
    return f"<table>{head}{body}</table>"


def _studies_section(studies):
    if not studies:
        return '<p class="sub">No study results found. Run a study, then rebuild.</p>'
    _vcolor = {"GO": STATUS["green"], "NO-GO": STATUS["red"], "CONDITIONAL": STATUS["yellow"]}
    out = []
    for s in studies:
        v = s.get("verdict") or {}
        dec = v.get("decision", "—")
        vc = _vcolor.get(dec, MUTED)
        reg = s.get("registration") or {}
        cols = s.get("columns", [])
        head = "<tr>" + "".join(f"<th>{_esc(c)}</th>" for c in cols) + "</tr>"
        body = ""
        for row in s.get("rows", []):
            body += "<tr>" + "".join(
                f'<td class="num">{_esc(row.get(c,""))}</td>' for c in cols) + "</tr>"
        out.append(
            f'<div class="card"><h3>{_esc(s["name"])} '
            f'<span class="verdict" style="background:{vc}">{_esc(dec)}</span></h3>'
            f'<div class="mode">{_esc(reg.get("question",""))}</div>'
            f'<div class="honest" style="font-style:normal">{_esc(v.get("rationale",""))}</div>'
            f'<details><summary>table ({s.get("n_rows",0)} rows · hash {_esc(s.get("byte_hash",""))})</summary>'
            f'<table>{head}{body}</table></details></div>')
    return '<div class="grid cards">' + "".join(out) + "</div>"


def render_html(model, title="Kronos Research Toolkit — research dashboard"):
    mode = model.get("mode", "public")
    mode_badge = ("public · firewall-clean (no economics)" if mode == "public"
                  else "confidential · internal")
    body = f"""
<div class="wrap">
  <h1>{_esc(title)}</h1>
  <div class="sub">toolkit v{_esc(model.get("toolkit_version"))} · seed {_esc(model.get("seed"))}
    · <span class="badge">{_esc(mode_badge)}</span></div>
  <div class="sub">Every number on this page is read live from the frozen anchors and engines — the single source of truth.</div>

  <h2>Gate status board</h2>
  {"".join(_gate_row(g) for g in model["gates"])}

  <h2>Design-point explorer</h2>
  <div class="grid cards">{"".join(_design_card(d) for d in model["design_points"])}</div>

  <h2>Extrapolation ledger — reach vs demonstrated</h2>
  {_ledger_table(model["extrapolation"])}

  <h2>Studies</h2>
  {_studies_section(model.get("studies", []))}

  <h2>Paper &amp; closure tracker</h2>
  {_papers_table(model["papers"])}

  <div class="foot">Generated by <code>kronos-viz build</code> from live toolkit state.
    Surrogates are tagged [T] and name the real code that retires them. This dashboard makes no economic claims.</div>
</div>
<script type="application/json" id="kronos-model">{json.dumps(model)}</script>
"""
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{_esc(title)}</title><style>{_CSS}</style></head>"
            f"<body>{body}</body></html>")
