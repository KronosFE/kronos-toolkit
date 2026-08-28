"""`kronos-viz` command line — regenerate the dashboard from live research outputs.

    kronos-viz build --out dashboard.html [--results DIR] [--confidential]
"""
import argparse
import sys


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="kronos-viz",
        description="Build the Kronos research dashboard from live toolkit state.")
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("build", help="build the HTML dashboard")
    b.add_argument("--out", default="kronos_dashboard.html",
                   help="output HTML path (default: kronos_dashboard.html)")
    b.add_argument("--results", default=None,
                   help="directory of study results (CSV + manifest) to include")
    b.add_argument("--confidential", action="store_true",
                   help="build the internal (confidential) view; default is public")
    b.add_argument("--title", default="Kronos Research Toolkit — research dashboard")

    args = p.parse_args(argv)
    if args.cmd != "build":
        p.print_help()
        return 1

    from .build import build_dashboard
    from ..report.guard import EconomicsLeak
    try:
        out = build_dashboard(args.out, results_dir=args.results,
                              public=not args.confidential, title=args.title)
    except EconomicsLeak as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    mode = "confidential" if args.confidential else "public (firewall-clean)"
    print(f"built {mode} dashboard -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
