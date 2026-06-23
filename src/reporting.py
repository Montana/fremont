from rich.console import Console
from rich.table import Table

console = Console()


def print_collection_table(rows: list[dict]) -> None:
    table = Table(title="MongoDB Collections")
    table.add_column("Collection", style="bold")
    table.add_column("Documents", justify="right")
    table.add_column("Indexes", justify="right")

    for row in rows:
        table.add_row(
            row["collection"],
            f'{row["documents"]:,}',
            str(row["index_count"]),
        )

    console.print(table)


def print_index_table(collection: str, indexes: list[dict]) -> None:
    table = Table(title=f"Indexes: {collection}")
    table.add_column("Name", style="bold")
    table.add_column("Keys")
    table.add_column("Unique")

    for idx in indexes:
        keys = ", ".join([f"{k}:{v}" for k, v in idx.get("key", {}).items()])
        table.add_row(idx.get("name", ""), keys, str(idx.get("unique", False)))

    console.print(table)


def print_explain_summary(summary: dict) -> None:
    table = Table(title="Explain Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    for key, value in summary.items():
        table.add_row(key, str(value))

    console.print(table)
