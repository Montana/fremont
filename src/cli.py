from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.syntax import Syntax

from fremont.analyzer import (
    benchmark_query,
    collection_indexes,
    database_overview,
    explain_query,
    summarize_explain,
)
from fremont.config import load_settings
from fremont.index_advisor import suggest_compound_index
from fremont.json_tools import mongo_shell_doc, parse_json_object
from fremont.mongo_client import get_database
from fremont.reporting import print_collection_table, print_explain_summary, print_index_table

app = typer.Typer(help="Fremont: MongoDB performance helper CLI.")
console = Console()


def connect(uri: Optional[str], db_name: Optional[str]):
    settings = load_settings(uri=uri, db=db_name)
    return get_database(settings.mongo_uri, settings.mongo_db)


@app.command()
def overview(
    uri: Optional[str] = typer.Option(None, help="MongoDB URI. Defaults to MONGO_URI."),
    db_name: Optional[str] = typer.Option(None, "--db", help="Database name. Defaults to MONGO_DB."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of a table."),
):
    db = connect(uri, db_name)
    rows = database_overview(db)

    if json_output:
        print(json.dumps(rows, indent=2, default=str))
    else:
        print_collection_table(rows)


@app.command()
def indexes(
    collection: str = typer.Argument(..., help="Collection name."),
    uri: Optional[str] = typer.Option(None, help="MongoDB URI. Defaults to MONGO_URI."),
    db_name: Optional[str] = typer.Option(None, "--db", help="Database name. Defaults to MONGO_DB."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of a table."),
):
    db = connect(uri, db_name)
    idx = collection_indexes(db, collection)

    if json_output:
        print(json.dumps(idx, indent=2, default=str))
    else:
        print_index_table(collection, idx)


@app.command()
def explain(
    collection: str = typer.Argument(..., help="Collection name."),
    filter_json: str = typer.Option("{}", "--filter", help="MongoDB filter JSON."),
    projection_json: str = typer.Option("", "--projection", help="Projection JSON."),
    sort_json: str = typer.Option("", "--sort", help="Sort JSON."),
    limit: int = typer.Option(0, "--limit", help="Limit result count."),
    uri: Optional[str] = typer.Option(None, help="MongoDB URI. Defaults to MONGO_URI."),
    db_name: Optional[str] = typer.Option(None, "--db", help="Database name. Defaults to MONGO_DB."),
    raw: bool = typer.Option(False, "--raw", help="Print full raw explain JSON."),
):
    db = connect(uri, db_name)
    filter_doc = parse_json_object(filter_json)
    projection_doc = parse_json_object(projection_json) if projection_json else None
    sort_doc = parse_json_object(sort_json) if sort_json else None

    result = explain_query(
        db=db,
        collection_name=collection,
        filter_doc=filter_doc,
        projection_doc=projection_doc,
        sort_doc=sort_doc,
        limit=limit,
    )

    if raw:
        syntax = Syntax(json.dumps(result, indent=2, default=str), "json")
        console.print(syntax)
        return

    print_explain_summary(summarize_explain(result))


@app.command()
def benchmark(
    collection: str = typer.Argument(..., help="Collection name."),
    filter_json: str = typer.Option("{}", "--filter", help="MongoDB filter JSON."),
    projection_json: str = typer.Option("", "--projection", help="Projection JSON."),
    sort_json: str = typer.Option("", "--sort", help="Sort JSON."),
    limit: int = typer.Option(0, "--limit", help="Limit result count."),
    runs: int = typer.Option(25, "--runs", help="How many times to run the query."),
    uri: Optional[str] = typer.Option(None, help="MongoDB URI. Defaults to MONGO_URI."),
    db_name: Optional[str] = typer.Option(None, "--db", help="Database name. Defaults to MONGO_DB."),
):
    if runs < 1:
        raise typer.BadParameter("--runs must be at least 1.")

    db = connect(uri, db_name)
    filter_doc = parse_json_object(filter_json)
    projection_doc = parse_json_object(projection_json) if projection_json else None
    sort_doc = parse_json_object(sort_json) if sort_json else None

    result = benchmark_query(
        db=db,
        collection_name=collection,
        filter_doc=filter_doc,
        projection_doc=projection_doc,
        sort_doc=sort_doc,
        limit=limit,
        runs=runs,
    )

    print(json.dumps(result, indent=2))


@app.command("suggest-index")
def suggest_index(
    collection: str = typer.Argument(..., help="Collection name."),
    filter_json: str = typer.Option("{}", "--filter", help="MongoDB filter JSON."),
    sort_json: str = typer.Option("", "--sort", help="Sort JSON."),
):
    filter_doc = parse_json_object(filter_json)
    sort_doc = parse_json_object(sort_json) if sort_json else {}

    index = suggest_compound_index(filter_doc, sort_doc)

    if not index:
        print("[yellow]No obvious index suggestion from this query shape.[/yellow]")
        return

    print("[bold green]Suggested index:[/bold green]")
    print(f"db.{collection}.createIndex({mongo_shell_doc(index)})")


if __name__ == "__main__":
    app()
