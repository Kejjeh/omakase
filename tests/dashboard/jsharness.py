"""Run a piece of the shipped dashboard JavaScript under node.

There is no JS test runner in this repo and no budget for adding one, so the
dashboard tests lift functions straight out of `docs/<cuisine>/index.html` and
execute them against a hand-rolled stub of the few DOM calls they make. The
point is that the assertion lands on the file that is actually served: editing
the HTML can break pytest, which is the only thing keeping these two pages
honest.
"""

import json
import pathlib
import shutil
import subprocess

import pytest

DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs"
DASHBOARDS = ["omakase", "italian"]  # the only two cuisines with an index.html


def source(cuisine: str) -> str:
    return (DOCS / cuisine / "index.html").read_text(encoding="utf-8")


def extract(src: str, signature: str) -> str:
    """Return the function starting at `signature`, matched by brace depth."""
    start = src.index(signature)
    depth = 0
    for i in range(src.index("{", start), len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start : i + 1]
    raise AssertionError(f"unbalanced braces after {signature!r}")


def run_node(script: str):
    """Execute `script` as an ES module and parse its stdout as JSON."""
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)
