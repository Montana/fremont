from typing import Any

RANGE_OPERATORS = {"$gt", "$gte", "$lt", "$lte", "$ne", "$nin", "$regex"}


def classify_filter_field(value: Any) -> str:
    if not isinstance(value, dict):
        return "equality"

    operators = set(value.keys())

    if operators & RANGE_OPERATORS:
        return "range"

    if "$in" in operators:
        return "equality"

    return "complex"


def decoto(indexes: list[dict]) -> list[dict]:
    """Find indexes whose key pattern is a strict prefix of another index.

    An index is redundant when every query it can satisfy can also be satisfied
    by a wider compound index that starts with the same keys. Returns a list of
    dicts with 'redundant' and 'covered_by' name strings. The built-in _id_
    index is always skipped.
    """
    specs = [
        (idx.get("name", ""), list((idx.get("key") or {}).items()))
        for idx in indexes
    ]

    redundant: list[dict] = []
    seen: set[str] = set()

    for i, (name_a, keys_a) in enumerate(specs):
        if name_a == "_id_" or not keys_a or name_a in seen:
            continue
        for j, (name_b, keys_b) in enumerate(specs):
            if i == j or name_b == "_id_" or not keys_b:
                continue
            if len(keys_a) < len(keys_b) and keys_b[: len(keys_a)] == keys_a:
                redundant.append({"redundant": name_a, "covered_by": name_b})
                seen.add(name_a)
                break

    return redundant


def palo_verde(
    query_shapes: list[dict[str, Any]],
    index_specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score how well existing indexes cover a list of query shapes.

    For each shape (keys: 'filter' and optionally 'sort'), builds the ideal
    compound index via the ESR heuristic, then checks whether any existing
    index's leading keys fully or partially cover it.

    Each result dict contains:
      - 'filter':     the original filter dict
      - 'sort':       the original sort dict (empty dict if omitted)
      - 'status':     'covered', 'partial', or 'uncovered'
      - 'covered_by': index name of the best match, or None
    """
    existing: list[tuple[str, list[tuple[str, int]]]] = [
        (idx.get("name", ""), list((idx.get("key") or {}).items()))
        for idx in index_specs
        if idx.get("name") != "_id_"
    ]

    results: list[dict[str, Any]] = []

    for shape in query_shapes:
        filter_doc: dict[str, Any] = shape.get("filter") or {}
        sort_doc: dict[str, int] = shape.get("sort") or {}

        ideal = list(suggest_compound_index(filter_doc, sort_doc).items())

        best_len = 0
        best_name: str | None = None

        for name, keys in existing:
            prefix_len = 0
            for i, pair in enumerate(ideal):
                if i >= len(keys) or keys[i] != pair:
                    break
                prefix_len += 1
            if prefix_len > best_len:
                best_len = prefix_len
                best_name = name

        if not ideal or best_len == 0:
            status = "uncovered"
            best_name = None
        elif best_len >= len(ideal):
            status = "covered"
        else:
            status = "partial"

        results.append(
            {"filter": filter_doc, "sort": sort_doc, "status": status, "covered_by": best_name}
        )

    return results


def suggest_compound_index(
    filter_doc: dict[str, Any],
    sort_doc: dict[str, int] | None = None,
) -> dict[str, int]:
    # Simple heuristic:
    # 1. equality fields first
    # 2. sort fields next
    # 3. range fields last
    sort_doc = sort_doc or {}

    equality_fields: list[str] = []
    range_fields: list[str] = []

    for field, value in filter_doc.items():
        if field.startswith("$"):
            continue

        kind = classify_filter_field(value)

        if kind == "equality":
            equality_fields.append(field)
        elif kind == "range":
            range_fields.append(field)

    index: dict[str, int] = {}

    for field in equality_fields:
        index[field] = 1

    for field, direction in sort_doc.items():
        if field not in index:
            index[field] = int(direction)

    for field in range_fields:
        if field not in index:
            index[field] = 1

    return index
