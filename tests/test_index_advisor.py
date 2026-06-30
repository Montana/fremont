"""Tests for the pure, DB-free helpers: the ESR index heuristic and JSON parsing.

These mirror the worked examples documented in the README so the docs and the
code can't silently drift apart.
"""

from __future__ import annotations

import pytest

from fremont.analyzer import mowry
from fremont.index_advisor import classify_filter_field, decoto, suggest_compound_index
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


# --- mowry -----------------------------------------------------------------


def _summary(
    *,
    stage: str = "FETCH -> IXSCAN",
    n_returned: int = 10,
    docs_examined: int = 10,
    keys_examined: int = 10,
) -> dict:
    return {
        "executionTimeMillis": 1,
        "nReturned": n_returned,
        "totalDocsExamined": docs_examined,
        "totalKeysExamined": keys_examined,
        "winningStage": stage,
        "indexUsed": "gamertag_1",
    }


def test_mowry_no_issues():
    result = mowry(_summary())
    assert result == ["No obvious issues detected."]


def test_mowry_collscan_detected():
    result = mowry(_summary(stage="COLLSCAN"))
    assert any("Collection scan" in msg for msg in result)


def test_mowry_high_docs_examined_ratio():
    result = mowry(_summary(n_returned=1, docs_examined=100, keys_examined=5))
    assert any("docs-examined-to-returned" in msg for msg in result)


def test_mowry_high_keys_examined_ratio():
    result = mowry(_summary(n_returned=1, docs_examined=5, keys_examined=100))
    assert any("keys-examined-to-returned" in msg for msg in result)


def test_mowry_multiple_findings():
    result = mowry(_summary(stage="COLLSCAN", n_returned=1, docs_examined=500, keys_examined=0))
    assert len(result) >= 2


def test_mowry_zero_returned_no_crash():
    result = mowry(_summary(n_returned=0, docs_examined=0, keys_examined=0))
    assert isinstance(result, list)
    assert len(result) >= 1


def test_mowry_empty_summary_no_crash():
    result = mowry({})
    assert result == ["No obvious issues detected."]


# --- decoto ----------------------------------------------------------------


def _idx(name: str, keys: dict) -> dict:
    return {"name": name, "key": keys}


def test_decoto_empty_list():
    assert decoto([]) == []


def test_decoto_single_index():
    assert decoto([_idx("gamertag_1", {"gamertag": 1})]) == []


def test_decoto_no_redundancy():
    indexes = [
        _idx("gamertag_1", {"gamertag": 1}),
        _idx("playlist_1", {"playlist": 1}),
    ]
    assert decoto(indexes) == []


def test_decoto_prefix_is_redundant():
    indexes = [
        _idx("gamertag_1", {"gamertag": 1}),
        _idx("gamertag_1_playlist_1", {"gamertag": 1, "playlist": 1}),
    ]
    result = decoto(indexes)
    assert result == [{"redundant": "gamertag_1", "covered_by": "gamertag_1_playlist_1"}]


def test_decoto_longer_prefix():
    indexes = [
        _idx("a_1_b_1", {"a": 1, "b": 1}),
        _idx("a_1_b_1_c_1", {"a": 1, "b": 1, "c": 1}),
    ]
    result = decoto(indexes)
    assert result == [{"redundant": "a_1_b_1", "covered_by": "a_1_b_1_c_1"}]


def test_decoto_id_index_ignored():
    indexes = [
        _idx("_id_", {"_id": 1}),
        _idx("gamertag_1", {"gamertag": 1}),
        _idx("gamertag_1_playlist_1", {"gamertag": 1, "playlist": 1}),
    ]
    result = decoto(indexes)
    assert all(r["redundant"] != "_id_" for r in result)
    assert len(result) == 1


def test_decoto_direction_mismatch_not_redundant():
    indexes = [
        _idx("played_at_1", {"played_at": 1}),
        _idx("played_at_neg1_kills_1", {"played_at": -1, "kills": 1}),
    ]
    assert decoto(indexes) == []


def test_decoto_no_double_report():
    indexes = [
        _idx("a_1", {"a": 1}),
        _idx("a_1_b_1", {"a": 1, "b": 1}),
        _idx("a_1_b_1_c_1", {"a": 1, "b": 1, "c": 1}),
    ]
    result = decoto(indexes)
    names = [r["redundant"] for r in result]
    assert names.count("a_1") == 1
