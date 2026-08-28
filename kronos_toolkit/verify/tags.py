"""Provenance tagging — [D] / [T] / [R] / [Q].

Every number the toolkit produces should be honest about where it came from.
This is the discipline that keeps a surrogate from ever being mistaken for a
high-fidelity result.

    [D] derived   — computed by real code / frozen engine (trustworthy result)
    [T] toy       — reduced-order SURROGATE standing in for a hi-fi code;
                    always carries `retired_by` (the real code that replaces it)
    [R] reference — taken from literature / an external anchor
    [Q] question  — provisional, needs verification before it is load-bearing
"""
from dataclasses import dataclass, field

VALID_TAGS = ("D", "T", "R", "Q")

_MEANING = {
    "D": "derived (real code / frozen engine)",
    "T": "toy surrogate (reduced-order stand-in)",
    "R": "reference (literature / external anchor)",
    "Q": "question (provisional, needs verification)",
}


@dataclass
class Tagged:
    """A value carrying its provenance."""
    value: object
    tag: str
    note: str = ""
    retired_by: str = ""       # for [T]: the real code that would replace this
    source: str = ""           # for [R]: the citation / anchor

    def __post_init__(self):
        if self.tag not in VALID_TAGS:
            raise ValueError(f"tag must be one of {VALID_TAGS}, got {self.tag!r}")
        if self.tag == "T" and not self.retired_by:
            raise ValueError(
                "a [T] surrogate must name the real code that retires it "
                "(retired_by=...)")

    @property
    def meaning(self):
        return _MEANING[self.tag]

    def __repr__(self):
        extra = ""
        if self.tag == "T" and self.retired_by:
            extra = f" retired_by={self.retired_by!r}"
        if self.tag == "R" and self.source:
            extra = f" source={self.source!r}"
        return f"[{self.tag}] {self.value!r}{extra}"


def derived(value, note=""):
    return Tagged(value, "D", note=note)


def surrogate(value, retired_by, note=""):
    """A reduced-order stand-in. Must name the hi-fi code that would replace it."""
    return Tagged(value, "T", note=note, retired_by=retired_by)


def reference(value, source, note=""):
    return Tagged(value, "R", note=note, source=source)


def question(value, note=""):
    return Tagged(value, "Q", note=note)
