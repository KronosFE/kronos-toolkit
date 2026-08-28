"""Build the dashboard: model -> (guard) -> HTML file."""
import os
from .data import build_model
from .render import render_html


def build_dashboard(out_path, results_dir=None, public=True,
                    title="Kronos Research Toolkit — research dashboard"):
    """Assemble the live model and write a self-contained HTML dashboard.

    Public mode runs the no-economics firewall over the whole model before render;
    if anything economic slipped in, it raises rather than emit a public page.
    """
    model = build_model(results_dir=results_dir, public=public)

    if public:
        from ..report.guard import assert_public_clean
        # Guard the human-facing content (not the DOIs/version metadata).
        assert_public_clean(
            dict(design_points=model["design_points"], gates=model["gates"],
                 extrapolation=model["extrapolation"], studies=model["studies"]),
            where="viz dashboard")

    htmltext = render_html(model, title=title)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(htmltext)
    return out_path
