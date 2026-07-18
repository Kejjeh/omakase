import pytest

from scripts.shared.places import (
    SIMILARITY_THRESHOLD,
    colliding_place_ids,
    is_trustworthy,
    name_similarity,
)


# --- name similarity ---

@pytest.mark.parametrize(
    ("ours", "theirs"),
    [
        ("Towa", "TOWA"),                                   # casing only
        ("Hoseki", "Hōseki"),                               # macron
        ("Mario's", "Mario's Restaurant of Arthur Avenue"),  # official name is longer
        ("Fratelli", "Fratelli Italian Restaurant"),
        ("Lombardo's of Bay Ridge", "Lombardo’s of Bay Ridge"),  # smart quote
    ],
)
def test_real_matches_are_trusted(ours, theirs):
    assert name_similarity(ours, theirs) >= SIMILARITY_THRESHOLD


@pytest.mark.parametrize(
    ("ours", "theirs"),
    [
        # Every one of these is a real substitution Places made for a closed
        # restaurant, and each would have flipped it back to open.
        ("ROKI", "RokuNana"),
        ("Tokyo Bar", "Sushi Tokyo Manhattan"),
        ("Robataya", "Sushi By Bou - East Village NYC"),
        ("Sushi Yugen", "YUGIN"),
        ("Inase", "Omakase Shihou - Upper West Side"),
        ("Sushi by Bae", "Momoya SoHo"),
        # The nastiest: a different restaurant whose name is one word away.
        ("Omakase by Teisui", "Omakase By Tento"),
        # Same street address, but a rebrand is not the same restaurant.
        ("Hiyake Omakase (Williamsburg)", "Hiyake Yakiniku BBQ"),
    ],
)
def test_substituted_matches_are_not_trusted(ours, theirs):
    assert name_similarity(ours, theirs) < SIMILARITY_THRESHOLD


def test_missing_names_score_zero():
    assert name_similarity(None, "Something") == 0.0
    assert name_similarity("Something", None) == 0.0
    assert name_similarity("", "") == 0.0


# --- place_id collisions ---

def test_two_restaurants_sharing_a_place_id_are_both_flagged():
    cache = {
        "Masa": {"place_id": "X", "google_name": "Bar Masa"},
        "Bar Masa": {"place_id": "X", "google_name": "Bar Masa"},
        "Other": {"place_id": "Y", "google_name": "Other"},
    }
    assert colliding_place_ids(cache) == {"Masa", "Bar Masa"}


def test_entries_absent_from_the_master_sheet_do_not_manufacture_collisions():
    # A stale cache entry sharing an id with a live one is not evidence that
    # the live one is wrong.
    cache = {
        "Live": {"place_id": "X"},
        "RemovedFromSheet": {"place_id": "X"},
    }
    assert colliding_place_ids(cache, {"Live"}) == set()


def test_missing_place_id_is_not_a_collision():
    cache = {"A": {"place_id": None}, "B": {"place_id": None}}
    assert colliding_place_ids(cache) == set()


# --- trust gate ---

def test_a_good_match_is_trustworthy():
    entry = {"place_id": "X", "google_name": "Shuko"}
    assert is_trustworthy("Shuko", entry)


def test_a_colliding_match_is_never_trustworthy_even_with_an_identical_name():
    # Collision is proof; name similarity is only inference. Proof wins.
    entry = {"place_id": "X", "google_name": "Omi Omakase"}
    assert not is_trustworthy("Omi Omakase", entry, colliding={"Omi Omakase", "That Place Omakase"})


def test_a_match_with_no_place_id_is_not_trustworthy():
    assert not is_trustworthy("Masuda Omakase", {"rating": 4.5, "google_name": "Masuda Omakase"})


def test_a_missing_entry_is_not_trustworthy():
    assert not is_trustworthy("Anything", None)


# --- collision reporting ---
#
# A shared place_id is proof of a wrong match, so it needs to surface on every
# pipeline run rather than waiting for someone to run an ad-hoc script.

def test_collision_groups_are_reported_largest_first():
    cache = {
        "A": {"place_id": "X"}, "B": {"place_id": "X"}, "C": {"place_id": "X"},
        "D": {"place_id": "Y"}, "E": {"place_id": "Y"},
        "F": {"place_id": "Z"},
    }
    from scripts.shared.places import collision_groups

    assert collision_groups(cache) == [["A", "B", "C"], ["D", "E"]]


def test_a_clean_cache_describes_no_collisions():
    from scripts.shared.places import describe_collisions

    assert describe_collisions({"A": {"place_id": "X"}, "B": {"place_id": "Y"}}) == ""


def test_collision_description_names_the_contended_listing():
    from scripts.shared.places import describe_collisions

    cache = {
        "Masa": {"place_id": "X", "google_name": "Bar Masa"},
        "Bar Masa": {"place_id": "X", "google_name": "Bar Masa"},
    }
    report = describe_collisions(cache)

    assert "Masa" in report and "Bar Masa" in report
    assert "wrong business" in report


def test_collision_description_respects_the_master_sheet():
    from scripts.shared.places import describe_collisions

    cache = {"Live": {"place_id": "X"}, "Removed": {"place_id": "X"}}

    assert describe_collisions(cache, {"Live"}) == ""
