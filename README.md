<img width="1881" height="1059" alt="Untitled design - 2026-06-23T154013 006" src="https://github.com/user-attachments/assets/f38a763d-2acc-499b-a55e-268ef3f85103" />

# Fremont

https://github.com/user-attachments/assets/f209c0d7-ac4d-4ddf-bd20-3de8afc172ed

Fremont is a remix of a MongoDB performance helper CLI demo built for HaloArchives.com.

Fremont helps you inspect MongoDB collections, read index definitions, run query explain plans, benchmark query shapes, and suggest basic compound indexes. The bundled demo loads a Halo 2 stats archive (`halo2_archive`) with four collections:

- `players`
- `matches`
- `player_stats`
- `playlists`

You point Fremont at any MongoDB instance, hand it a collection and a query shape (filter / projection / sort / limit), and it tells you what the planner is doing, how fast it runs, and what index would help.

## Features

- **`overview`** — list every collection with document and index counts.
- **`indexes`** — dump the index definitions on a single collection.
- **`explain`** — run a query's explain plan and summarize the winning stage, the index used, and docs/keys examined.
- **`benchmark`** — execute a query shape N times and report min / max / avg / median latency.
- **`suggest-index`** — turn a filter + sort into a recommended compound index, ordered by the ESR (equality, sort, range) rule.

Output is rendered with [Rich](https://github.com/Textualize/rich) tables, and every read command also supports `--json` (or `--raw` for `explain`) for piping into other tools.

## Requirements

- Python 3.10+
- A reachable MongoDB instance (Docker Compose config is included)
- Python deps: `typer`, `rich`, `pymongo`, `python-dotenv` (plus `ruff` and `pytest` for development)

## What Fremont does

```bash
fremont overview --db halo2_archive
fremont indexes player_stats --db halo2_archive
fremont explain matches --db halo2_archive --filter '{"map":"Lockout","playlist":"MLG"}' --sort '{"played_at":-1}' --limit 5
fremont benchmark player_stats --db halo2_archive --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' --sort '{"kills":-1}' --limit 10 --runs 50
fremont suggest-index player_stats --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' --sort '{"played_at":-1}'
```

## Install locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Start MongoDB

```bash
docker compose up -d
```

This launches `mongo:7` on `localhost:27017` with a persistent named volume.

## Seed the Halo 2 demo database

```bash
python seed.py
```

The seed script drops and rebuilds `halo2_archive` with 5,000 players, 50,000 matches, 200,000 player stat lines, and 4 playlists, along with a realistic set of single-field and compound indexes. The random seed is fixed (`117`) so the data is reproducible between runs.

## Configuration

Fremont reads connection settings from CLI flags first, then environment variables, then sensible defaults. A `.env` file in the project root is loaded automatically.

| Setting     | Flag    | Env var     | Default                       |
| ----------- | ------- | ----------- | ----------------------------- |
| MongoDB URI | `--uri` | `MONGO_URI` | `mongodb://localhost:27017`   |
| Database    | `--db`  | `MONGO_DB`  | `halo2_archive`               |

Example `.env`:

```dotenv
MONGO_URI=mongodb://localhost:27017
MONGO_DB=halo2_archive
```

## Run the demo

```bash
fremont overview --db halo2_archive
```

Example output:

```text
              MongoDB Collections
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┓
┃ Collection   ┃ Documents ┃ Indexes ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━┩
│ matches      │    50,000 │       4 │
│ players      │     5,000 │       3 │
│ player_stats │   200,000 │       6 │
│ playlists    │         4 │       2 │
└──────────────┴───────────┴─────────┘
```

## Command reference

### `overview`

List all collections in the database with estimated document counts and index counts.

```bash
fremont overview [--db halo2_archive] [--uri ...] [--json]
```

### `indexes`

Show the index definitions (name, keys, uniqueness) for one collection.

```bash
fremont indexes <collection> [--db halo2_archive] [--uri ...] [--json]
```

### `explain`

Run a query's explain plan and print a summary, or the full plan with `--raw`.

```bash
fremont explain matches \
  --db halo2_archive \
  --filter '{"map":"Lockout","playlist":"MLG"}' \
  --sort '{"played_at":-1}' \
  --limit 5
```

Options: `--filter`, `--projection`, `--sort`, `--limit`, `--uri`, `--db`, `--raw`.

The summary surfaces `executionTimeMillis`, `nReturned`, `totalKeysExamined`, `totalDocsExamined`, the winning stage chain (for example `LIMIT -> SORT -> FETCH -> IXSCAN`), and the name of the index that was used.

### `benchmark`

Run a query shape repeatedly and report timing statistics.

```bash
fremont benchmark player_stats \
  --db halo2_archive \
  --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
  --sort '{"kills":-1}' \
  --limit 10 \
  --runs 50
```

Options: `--filter`, `--projection`, `--sort`, `--limit`, `--runs` (default `25`), `--uri`, `--db`.

Output:

```json
{
  "runs": 50,
  "min_ms": 0.412,
  "max_ms": 3.118,
  "avg_ms": 0.731,
  "median_ms": 0.655,
  "returned_count_last_run": 10
}
```

### `suggest-index`

Translate a filter and sort into a candidate compound index. This command works purely on the query shape and does not need a live connection.

```bash
fremont suggest-index player_stats \
  --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
  --sort '{"played_at":-1}'
```

Output:

```js
db.player_stats.createIndex({ "gamertag": 1, "playlist": 1, "played_at": -1 })
```

## How index suggestions work

`suggest-index` follows the standard MongoDB **ESR** ordering rule and builds the key in three passes:

1. **Equality** fields first — exact matches and `$in` clauses.
2. **Sort** fields next, in the order and direction you requested.
3. **Range** fields last — anything using `$gt`, `$gte`, `$lt`, `$lte`, `$ne`, `$nin`, or `$regex`.

Fields already placed by an earlier pass are not duplicated, and top-level `$` operators (like `$or`) are skipped. The result is a heuristic starting point, not a guarantee — always validate a suggestion with `explain` and `benchmark` against your real data.

## Makefile shortcuts

```bash
make install     # pip install -e ".[dev]"
make lint        # ruff check .
make test        # pytest -q
make demo-up     # docker compose up -d
make demo-seed   # seed the halo2_archive database
make demo        # up + seed + overview, end to end
```

## Repo layout

```text
fremont/
  src/
    analyzer.py        # overview, indexes, explain, benchmark logic
    cli.py             # Typer command definitions
    config.py          # settings + .env loading
    index_advisor.py   # ESR compound-index heuristic
    json_tools.py      # JSON parsing + mongo-shell rendering
    mongo_client.py    # PyMongo connection helper
    reporting.py       # Rich table rendering
  seed.py              # builds the halo2_archive demo data
  docker-compose.yml   # mongo:7 service
  Makefile             # install / lint / test / demo targets
  fremont.mp4          # demo recording
  README.md
```

## Notes

- Document counts in `overview` come from `estimatedDocumentCount()`, which is fast but approximate on large collections.
- Fremont issues read-only operations against your data; `suggest-index` only prints a `createIndex` statement, it never runs it.
- The demo data is gaming-flavored, but nothing in Fremont is Halo-specific — point it at any MongoDB database and any collection.
