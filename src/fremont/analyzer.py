from __future__ import annotations

import statistics
import time
from typing import Any

from pymongo.database import Database


def database_overview(db: Database) -> list[dict[str, Any]]:
    rows = []

    for name in db.list_collection_names():
        collection = db[name]

        try:
            documents = collection.estimated_document_count()
        except Exception:
            documents = -1

        try:
            indexes = list(collection.list_indexes())
            index_count = len(indexes)
        except Exception:
            index_count = -1

        rows.append(
            {
                "collection": name,
                "documents": documents,
                "index_count": index_count,
            }
        )

    return sorted(rows, key=lambda row: row["collection"])


def collection_indexes(db: Database, collection_name: str) -> list[dict[str, Any]]:
    return list(db[collection_name].list_indexes())


def explain_query(
    db: Database,
    collection_name: str,
    filter_doc: dict[str, Any],
    projection_doc: dict[str, Any] | None = None,
    sort_doc: dict[str, int] | None = None,
    limit: int = 0,
) -> dict[str, Any]:
    collection = db[collection_name]
    cursor = collection.find(filter_doc, projection_doc or None)

    if sort_doc:
        cursor = cursor.sort(list(sort_doc.items()))

    if limit:
        cursor = cursor.limit(limit)

    return cursor.explain()


def summarize_explain(explain: dict[str, Any]) -> dict[str, Any]:
    execution = explain.get("executionStats", {})
    query_planner = explain.get("queryPlanner", {})
    winning_plan = query_planner.get("winningPlan", {})

    return {
        "executionTimeMillis": execution.get("executionTimeMillis"),
        "nReturned": execution.get("nReturned"),
        "totalKeysExamined": execution.get("totalKeysExamined"),
        "totalDocsExamined": execution.get("totalDocsExamined"),
        "winningStage": extract_stage(winning_plan),
        "indexUsed": extract_index_name(winning_plan),
    }


def extract_stage(plan: dict[str, Any]) -> str:
    if not isinstance(plan, dict):
        return "unknown"

    if "stage" in plan:
        stage = plan["stage"]
        child = plan.get("inputStage")
        if child:
            return f"{stage} -> {extract_stage(child)}"
        return stage

    if "queryPlan" in plan:
        return extract_stage(plan["queryPlan"])

    if "inputStage" in plan:
        return extract_stage(plan["inputStage"])

    if "inputStages" in plan and plan["inputStages"]:
        return ", ".join(extract_stage(stage) for stage in plan["inputStages"])

    return "unknown"


def extract_index_name(plan: dict[str, Any]) -> str:
    if not isinstance(plan, dict):
        return ""

    if "indexName" in plan:
        return plan["indexName"]

    for key in ("queryPlan", "inputStage"):
        if key in plan:
            found = extract_index_name(plan[key])
            if found:
                return found

    for stage in plan.get("inputStages", []):
        found = extract_index_name(stage)
        if found:
            return found

    return ""


def benchmark_query(
    db: Database,
    collection_name: str,
    filter_doc: dict[str, Any],
    projection_doc: dict[str, Any] | None = None,
    sort_doc: dict[str, int] | None = None,
    limit: int = 0,
    runs: int = 25,
) -> dict[str, Any]:
    collection = db[collection_name]
    timings_ms: list[float] = []
    returned_counts: list[int] = []

    for _ in range(runs):
        start = time.perf_counter()

        cursor = collection.find(filter_doc, projection_doc or None)

        if sort_doc:
            cursor = cursor.sort(list(sort_doc.items()))

        if limit:
            cursor = cursor.limit(limit)

        docs = list(cursor)
        elapsed = (time.perf_counter() - start) * 1000

        timings_ms.append(elapsed)
        returned_counts.append(len(docs))

    return {
        "runs": runs,
        "min_ms": round(min(timings_ms), 3),
        "max_ms": round(max(timings_ms), 3),
        "avg_ms": round(statistics.mean(timings_ms), 3),
        "median_ms": round(statistics.median(timings_ms), 3),
        "returned_count_last_run": returned_counts[-1] if returned_counts else 0,
    }
