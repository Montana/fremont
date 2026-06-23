import json
from typing import Any


def parse_json_object(value: str | None, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None or value.strip() == "":
        return default or {}

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError('Expected a JSON object, for example: {"map":"Lockout"}')

    return parsed


def mongo_shell_doc(doc: dict[str, Any]) -> str:
    parts = []

    for key, value in doc.items():
        if isinstance(value, str):
            rendered = f'"{value}"'
        else:
            rendered = json.dumps(value)
        parts.append(f'"{key}": {rendered}')

    return "{ " + ", ".join(parts) + " }"
