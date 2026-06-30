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
