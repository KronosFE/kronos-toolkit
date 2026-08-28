"""Standardized study scaffold.

Every Kronos study follows the same spine so results are comparable and
reproducible:

    pre_register  — declare question, hypothesis, method, gate BEFORE running
    run           — execute the sweep/evaluation (deterministic, seeded)
    to_csv        — write the results table
    manifest      — write a two-tier reproducibility manifest (byte + tolerance)
    verdict       — record the honest GO / NO-GO / CONDITIONAL against the gate

A Study writing to a public directory is economics-guarded automatically.
"""
import os
import csv
import json
import hashlib
from datetime import datetime, timezone
from .. import SEED, __version__
from .guard import guard


def _hash_rows(rows, keys):
    """Deterministic byte hash of the results table (tier-1 reproducibility)."""
    h = hashlib.sha256()
    for row in rows:
        for k in keys:
            h.update(f"{k}={row.get(k)!r};".encode())
        h.update(b"\n")
    return h.hexdigest()


class Study:
    def __init__(self, name, out_dir, public=True, seed=SEED, stamp=None):
        self.name = name
        self.out_dir = out_dir
        self.public = public
        self.seed = seed
        # No Date.now equivalent in-script determinism concern here; a real run
        # stamps wall time. Tests pass an explicit stamp for reproducibility.
        self.stamp = stamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.registration = None
        self.rows = []
        self.columns = []
        self._verdict = None
        os.makedirs(out_dir, exist_ok=True)

    # --- 1. pre-registration ----------------------------------------------
    def pre_register(self, question, hypothesis, method, gate, tags=None):
        """Declare the study intent before any result exists."""
        self.registration = dict(
            question=question, hypothesis=hypothesis, method=method,
            gate=gate, tags=tags or [],
        )
        if self.public:
            guard(self.registration, public=True, where="pre-registration")
        return self

    # --- 2. run ------------------------------------------------------------
    def run(self, fn, cases, columns):
        """Run fn(**case) for each case; collect the listed output columns.

        fn returns a dict (a core/hifi/neutronics result, or a Tagged.value).
        """
        self.columns = list(columns)
        self.rows = []
        for case in cases:
            out = fn(**case)
            if hasattr(out, "value"):        # unwrap a Tagged result
                tag = out.tag
                out = dict(out.value)
                out.setdefault("_tag", tag)
            row = dict(case)
            for c in columns:
                if c not in row:
                    row[c] = out.get(c)
            self.rows.append(row)
        return self

    def add_rows(self, rows, columns):
        """Attach pre-computed rows (for studies that produce their own table)."""
        self.columns = list(columns)
        self.rows = list(rows)
        return self

    # --- 3. csv ------------------------------------------------------------
    def to_csv(self, filename=None):
        path = os.path.join(self.out_dir, filename or f"{self.name}.csv")
        if self.public:
            guard(self.rows, public=True, where="csv")
        keys = list(self.columns)
        # include any input keys present in the first row but not in columns
        if self.rows:
            for k in self.rows[0]:
                if k not in keys and not k.startswith("_"):
                    keys.append(k)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for row in self.rows:
                w.writerow(row)
        return path

    # --- 4. manifest -------------------------------------------------------
    def manifest(self, filename=None, anchors=None):
        """Two-tier reproducibility manifest: byte hash + declared tolerances."""
        keys = list(self.columns)
        man = dict(
            study=self.name,
            toolkit_version=__version__,
            seed=self.seed,
            stamp=self.stamp,
            public=self.public,
            registration=self.registration,
            n_rows=len(self.rows),
            columns=keys,
            tier1_byte_hash=_hash_rows(self.rows, keys),
            tier2_tolerances=anchors or {},
            verdict=self._verdict,
        )
        if self.public:
            guard(man, public=True, where="manifest")
        path = os.path.join(self.out_dir, filename or f"{self.name}.manifest.json")
        with open(path, "w") as f:
            json.dump(man, f, indent=2, default=str)
        return path

    # --- 5. verdict --------------------------------------------------------
    def verdict(self, decision, rationale, evidence=None):
        """Record the honest verdict against the pre-registered gate.

        decision: 'GO' | 'NO-GO' | 'CONDITIONAL'
        """
        if decision not in ("GO", "NO-GO", "CONDITIONAL"):
            raise ValueError("decision must be GO / NO-GO / CONDITIONAL")
        self._verdict = dict(decision=decision, rationale=rationale,
                             evidence=evidence or {})
        if self.public:
            guard(self._verdict, public=True, where="verdict")
        return self._verdict
