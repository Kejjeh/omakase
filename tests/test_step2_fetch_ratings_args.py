"""step2_fetch_ratings.py bills Google Places, so its arguments must be strict.

It used to read `sys.argv` by hand at import time and import the API key at
import time too. A flag it did not know was ignored, and even `--dry-run`
needed the key file. A sibling project's ratings script ran a real, billed
fetch because a `--dry-run` it did not support was silently ignored.

These tests wire the key loader and `requests.get` to fail loudly, so a
regression reads as "tried to read the key", not as a bill.
"""
import json

import pytest

import scripts.step2_fetch_ratings as step2


class Tripwire(AssertionError):
    pass


@pytest.fixture
def no_spend(monkeypatch):
    calls = []

    def trip(what):
        def _f(*a, **k):
            calls.append(what)
            raise Tripwire(f"{what} was called")
        return _f

    monkeypatch.setattr(step2, "api_key", trip("api_key"))
    monkeypatch.setattr(step2.requests, "get", trip("requests.get"))
    monkeypatch.setattr(step2, "save_cache", trip("save_cache"))
    return calls


@pytest.mark.parametrize("argv", [
    ["--dry-runn"],
    ["--bogus"],
    ["--cuisine", "sushi"],
    ["--cuisine"],                 # the old parser fell back to omakase here
    ["--cuisine", "italian", "extra"],
])
def test_an_unknown_argument_exits_nonzero_before_any_key_or_network(
        argv, no_spend, capsys):
    with pytest.raises(SystemExit) as e:
        step2.main(argv)
    assert e.value.code == 2
    assert no_spend == []
    assert "usage:" in capsys.readouterr().err


def test_valid_invocations_parse_to_the_old_defaults():
    a = step2.parse_args([])
    assert (a.cuisine, a.repair, a.force, a.dry_run) == ("omakase", False, False, False)
    b = step2.parse_args(["-c", "italian", "--repair"])
    assert (b.cuisine, b.repair) == ("italian", True)


@pytest.mark.parametrize("cuisine", ["omakase", "italian", "philly", "kensington"])
def test_dry_run_reads_no_key_and_sends_nothing(cuisine, no_spend, capsys):
    step2.main(["--cuisine", cuisine, "--dry-run"])
    out = capsys.readouterr().out
    assert "billed call(s)" in out and "Estimated cost: $" in out
    assert no_spend == []


def test_dry_run_count_and_cost_follow_the_run_loop_decision(
        no_spend, monkeypatch, tmp_path, capsys):
    """The count comes from the same action_for() the billed loop uses."""
    restaurants = tmp_path / "restaurants.json"
    restaurants.write_text(json.dumps([
        {"name": "Cached"}, {"name": "New"}, {"name": "Pinned"},
        {"name": "NoListing"}, {"name": "OldGeo"},
    ]), encoding="utf-8")
    full = {"rating": 4.5, "review_count": 10, "lat": 1.0, "lng": 2.0,
            "address": "a", "place_id": "P1"}
    cache = {"Cached": full,
             "Pinned": {**full, "place_id": "WRONG"},
             "NoListing": {**full, "place_id": "WRONG2"},
             "OldGeo": {**full, "place_id": "P3", "lat": None}}
    monkeypatch.setattr(step2, "configure", lambda a: (
        setattr(step2, "RESTAURANTS_PATH", restaurants),
        setattr(step2, "DRY_RUN", a.dry_run),
        setattr(step2, "FORCE", a.force),
        setattr(step2, "REPAIR", a.repair),
        setattr(step2, "CUISINE", "omakase")))
    monkeypatch.setattr(step2, "load_cache", lambda: cache)
    monkeypatch.setattr(step2, "load_overrides",
                        lambda: {"Pinned": "RIGHT", "NoListing": None})

    step2.main(["--dry-run"])
    out = capsys.readouterr().out
    # New -> Text Search; Pinned -> Details; NoListing -> free detach.
    assert "2 billed call(s) — 1 Text Search, 1 Details" in out
    assert "1 null pin(s) detached" in out
    assert "Estimated cost: $0.06" in out

    step2.main(["--dry-run", "--repair"])     # + OldGeo re-fetched
    assert "3 billed call(s) — 2 Text Search, 1 Details" in capsys.readouterr().out

    step2.main(["--dry-run", "--force"])      # + Cached and OldGeo
    out = capsys.readouterr().out
    assert "4 billed call(s) — 3 Text Search, 1 Details" in out
    assert "Estimated cost: $0.13" in out
    assert no_spend == []
