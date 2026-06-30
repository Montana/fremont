"""Tests for the pure, DB-free helpers: the ESR index heuristic and JSON parsing.

These mirror the worked examples documented in the README so the docs and the
code can't silently drift apart.
"""

from __future__ import annotations

import pytest

from fremont.index_advisor import classify_filter_field, suggest_compound_index
from fremont.json_tools import mongo_shell_doc, parse_json_object


# --- classify_filter_field -------------------------------------------------


def test_scalar_is_equality():
    assert classify_filter_field("MLG") == "equality"
    assert classify_filter_field(42) == "equality"


def test_in_is_equality():
    assert classify_filter_field({"$in": ["MLG", "Team Slayer"]}) == "equality"


@pytest.mark.parametrize("op", ["$gt", "$gte", "$lt", "$lte", "$ne", "$nin", "$regex"])
def test_range_operators(op):
    assert classify_filter_field({op: 5}) == "range"


def test_unknown_operator_is_complex():
    assert classify_filter_field({"$exists": True}) == "complex"
    assert classify_filter_field({"$elemMatch": {"x": 1}}) == "complex"


# --- suggest_compound_index (README worked examples) -----------------------


def test_equality_only():
    idx = suggest_compound_index({"gamertag": "Crafty Kisses", "playlist": "MLG"})
    assert idx == {"gamertag": 1, "playlist": 1}


def test_equality_plus_sort():
    idx = suggest_compound_index(
        {"gamertag": "Crafty Kisses", "playlist": "MLG"},
        {"played_at": -1},
    )
    assert idx == {"gamertag": 1, "playlist": 1, "played_at": -1}


def test_esr_order_equality_sort_range():
    # range field (kills) must land after the sort field, with direction 1
    idx = suggest_compound_index(
        {"map": "Lockout", "kills": {"$gte": 25}},
        {"played_at": -1},
    )
    assert list(idx.items()) == [("map", 1), ("played_at", -1), ("kills", 1)]


def test_in_counts_as_equality_and_stays_in_front():
    idx = suggest_compound_index(
        {"playlist": {"$in": ["MLG", "Team Slayer"]}, "winner_team": "red"}
    )
    assert idx == {"playlist": 1, "winner_team": 1}


def test_complex_fields_are_dropped():
    idx = suggest_compound_index({"meta": {"$exists": True}, "playlist": "MLG"})
    assert idx == {"playlist": 1}


def test_dollar_top_level_keys_ignored():
    idx = suggest_compound_index({"$or": [{"a": 1}], "playlist": "MLG"})
    assert idx == {"playlist": 1}


def test_first_placement_wins():
    # field appears as equality and again in sort; equality direction (1) is kept
    idx = suggest_compound_index({"playlist": "MLG"}, {"playlist": -1})
    assert idx == {"playlist": 1}


def test_no_suggestion_is_empty():
    assert suggest_compound_index({}, {}) == {}
    assert suggest_compound_index({"meta": {"$exists": True}}) == {}


# --- json_tools ------------------------------------------------------------


def test_parse_empty_returns_default():
    assert parse_json_object("") == {}
    assert parse_json_object(None) == {}
    assert parse_json_object("", default={"a": 1}) == {"a": 1}


def test_parse_valid_object():
    assert parse_json_object('{"map":"Lockout"}') == {"map": "Lockout"}


def test_parse_rejects_non_object():
    with pytest.raises(ValueError):
        parse_json_object("[1, 2, 3]")


def test_parse_rejects_bad_json():
    with pytest.raises(ValueError):
        parse_json_object("{not json}")


def test_mongo_shell_doc_rendering():
    rendered = mongo_shell_doc({"gamertag": 1, "playlist": 1, "played_at": -1})
    assert rendered == '{ "gamertag": 1, "playlist": 1, "played_at": -1 }'
