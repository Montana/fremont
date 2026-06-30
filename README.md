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

## Feel Right At Home
 
If you already know MongoDB, there's nothing new to learn — Fremont speaks the language you're used to, in both directions.
 
- **Filters, projections, and sorts are just MongoDB query JSON.** Whatever you'd hand to `db.collection.find()`, you hand to Fremont: `--filter '{"map":"Lockout","playlist":"MLG"}'`, `--sort '{"played_at":-1}'`, `--projection '{"kills":1}'`. No bespoke query DSL, no wrapper syntax.
- **Connections are plain URIs.** `--uri` (or `MONGO_URI`) takes the same `mongodb://...` connection string you'd give `mongosh` or any official driver.
- **`explain` is the real plan.** Fremont calls PyMongo's `.explain()` and summarizes it; add `--raw` to get the full, untouched planner output exactly as the server returns it.
- **`suggest-index` gives you copy-paste shell.** The suggestion comes out as a ready-to-run `db.<collection>.createIndex({ ... })` statement — drop it straight into `mongosh` or Compass.
```text
$ fremont suggest-index player_stats \
    --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
    --sort '{"played_at":-1}'
 
Suggested index:
db.player_stats.createIndex({ "gamertag": 1, "playlist": 1, "played_at": -1 })
```
 
That's it — paste it into your shell and you're done. Fremont is a guide, not a new tool to learn.
 
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

## `mowry`

`mowry` is a diagnostic function that reads an explain summary (the dict returned by `summarize_explain`) and returns a list of plain-English observations. It is the fastest way to go from an explain result to an actionable verdict without reading the raw numbers yourself.

### What it checks

| Condition | Finding |
| --------- | ------- |
| Winning stage contains `COLLSCAN` | Collection scan — no index is being used |
| `totalDocsExamined / nReturned > 10` | Index exists but isn't selective enough |
| `totalKeysExamined / nReturned > 10` | A more specific compound index may help |
| None of the above | `"No obvious issues detected."` |

### Usage

`mowry` is a Python-level helper, not a CLI command. Call it after `explain_query` + `summarize_explain`:

```python
from fremont.analyzer import explain_query, mowry, summarize_explain
from fremont.mongo_client import get_database

db = get_database("mongodb://localhost:27017", "halo2_archive")
raw = explain_query(db, "player_stats", {"gamertag": "Crafty Kisses", "playlist": "MLG"})
summary = summarize_explain(raw)
for finding in mowry(summary):
    print(finding)
```

Example output when no index covers the query:

```
Collection scan detected — no index is being used for this query shape.
```

Example output when a covering index is in place:

```
No obvious issues detected.
```

`mowry` never touches the database; it reasons purely over the summary dict you pass in.

## `decoto`

`decoto` scans a collection's index list and identifies any index whose key pattern is a strict prefix of another. Such an index is redundant — every query it can serve can also be served by the wider compound index — and is a candidate for removal to reduce write overhead.

### How prefix detection works

Index **A** is flagged as redundant when there exists an index **B** whose leading keys match A's keys exactly, in the same order and direction. For example:

| Index A | Index B | Verdict |
| ------- | ------- | ------- |
| `{ gamertag: 1 }` | `{ gamertag: 1, playlist: 1 }` | A is redundant |
| `{ a: 1, b: 1 }` | `{ a: 1, b: 1, c: 1 }` | A is redundant |
| `{ played_at: 1 }` | `{ played_at: -1, kills: 1 }` | not redundant (direction differs) |
| `{ gamertag: 1 }` | `{ playlist: 1, gamertag: 1 }` | not redundant (order differs) |

The `_id_` index is always skipped.

### Usage

```python
from fremont.analyzer import collection_indexes
from fremont.index_advisor import decoto
from fremont.mongo_client import get_database

db = get_database("mongodb://localhost:27017", "halo2_archive")
indexes = collection_indexes(db, "player_stats")
for finding in decoto(indexes):
    print(f"  {finding['redundant']} is covered by {finding['covered_by']}")
```

Example output:

```
  gamertag_1 is covered by gamertag_1_playlist_1_played_at_neg1
```

An empty list means no redundancy was detected. `decoto` never queries the database; it works entirely from the index metadata you pass in.

## `paseo padre`

`paseo padre` compares two `benchmark_query` results — a *before* and an *after* — and returns delta statistics plus a plain-English verdict. It is the natural last step after adding an index: benchmark the query, create the index, benchmark again, then call `paseo_padre` to quantify the change.

### Return value

| Key | Type | Description |
| --- | ---- | ----------- |
| `avg_delta_ms` | float | `after.avg_ms − before.avg_ms` |
| `avg_change_pct` | float | Percent change in average latency |
| `median_delta_ms` | float | `after.median_ms − before.median_ms` |
| `median_change_pct` | float | Percent change in median latency |
| `verdict` | str | `"improved"`, `"regressed"`, or `"unchanged"` |

The verdict threshold is **5 %** on average latency — smaller swings are reported as `"unchanged"`.

### Usage

```python
from fremont.analyzer import benchmark_query, paseo_padre
from fremont.mongo_client import get_database

db = get_database("mongodb://localhost:27017", "halo2_archive")
query = dict(
    collection_name="player_stats",
    filter_doc={"gamertag": "Crafty Kisses", "playlist": "MLG"},
    sort_doc={"played_at": -1},
    limit=10,
    runs=50,
)

before = benchmark_query(db, **query)
# → create your index here, e.g. via mongosh or Compass
after = benchmark_query(db, **query)

report = paseo_padre(before, after)
print(report)
```

Example output after adding a compound index:

```json
{
  "avg_delta_ms": -4.312,
  "avg_change_pct": -83.1,
  "median_delta_ms": -4.1,
  "median_change_pct": -81.4,
  "verdict": "improved"
}
```

`paseo_padre` is a pure offline function — it only operates on the two dicts you pass in and never touches the database.

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
 
`suggest-index` builds a candidate compound index from a query shape by following MongoDB's **ESR** rule — **E**quality, then **S**ort, then **R**ange. It never touches the database; it reasons purely about the `--filter` and `--sort` you give it.
 
### 1. Classify each filter field
 
Every top-level field in the filter is bucketed by the shape of its value:
 
| Filter value                          | Classified as | Goes into the index? |
| ------------------------------------- | ------------- | -------------------- |
| A plain scalar, e.g. `"MLG"` or `42`  | equality      | yes                  |
| `{"$in": [...]}`                      | equality      | yes                  |
| `{"$gt"/"$gte"/"$lt"/"$lte": ...}`    | range         | yes                  |
| `{"$ne": ...}`, `{"$nin": [...]}`     | range         | yes                  |
| `{"$regex": ...}`                     | range         | yes                  |
| Anything else, e.g. `{"$exists": true}`, `{"$elemMatch": ...}` | complex | no (skipped) |
 
Any top-level key that itself starts with `$` (such as `$or` or `$and`) is ignored — the heuristic only reasons about straightforward field-level predicates.
 
### 2. Assemble the key in three passes
 
1. **Equality** fields first, each with direction `1`, in the order they appear in the filter.
2. **Sort** fields next, using the exact direction you requested (`1` or `-1`).
3. **Range** fields last, each with direction `1`.
A field is only placed once: if it already appears from an earlier pass, later passes skip it (so the first placement wins, and its direction is kept). Fields classified as *complex* are dropped entirely. If nothing survives, the command prints `No obvious index suggestion from this query shape.` instead of an index.
 
### Worked examples
 
Equality only:
 
```bash
fremont suggest-index player_stats --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}'
# db.player_stats.createIndex({ "gamertag": 1, "playlist": 1 })
```
 
Equality + sort (the classic ESR shape):
 
```bash
fremont suggest-index player_stats \
  --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
  --sort '{"played_at":-1}'
# db.player_stats.createIndex({ "gamertag": 1, "playlist": 1, "played_at": -1 })
```
 
Equality + sort + range — note the range field (`kills`) lands after the sort field, and ranges always use direction `1`:
 
```bash
fremont suggest-index player_stats \
  --filter '{"map":"Lockout","kills":{"$gte":25}}' \
  --sort '{"played_at":-1}'
# db.player_stats.createIndex({ "map": 1, "played_at": -1, "kills": 1 })
```
 
`$in` counts as equality, so it stays at the front:
 
```bash
fremont suggest-index matches \
  --filter '{"playlist":{"$in":["MLG","Team Slayer"]},"winner_team":"red"}'
# db.matches.createIndex({ "playlist": 1, "winner_team": 1 })
```
 
### Limitations
 
This is a deliberately simple heuristic and a *starting point*, not a tuned recommendation. It does not:
 
- look at your existing indexes, so it may suggest something you already have or a redundant prefix;
- consider field cardinality or selectivity (it can't know `gamertag` is more selective than `region`);
- account for multikey/array fields, partial or sparse indexes, or covered-query projections;
- descend into `$or` / `$and` branches.
Always confirm a suggestion against real data with `explain` (to verify the planner actually uses it) and `benchmark` (to confirm it's faster) before creating it in production.
 
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
    fremont/
      __init__.py
      analyzer.py        # overview, indexes, explain, benchmark logic
      cli.py             # Typer command definitions
      config.py          # settings + .env loading
      index_advisor.py   # ESR compound-index heuristic
      json_tools.py      # JSON parsing + mongo-shell rendering
      mongo_client.py    # PyMongo connection helper
      reporting.py       # Rich table rendering
  tests/
    test_index_advisor.py  # offline unit tests (ESR heuristic + JSON tools)
  seed.py              # builds the halo2_archive demo data
  docker-compose.yml   # mongo:7 service
  Makefile             # install / lint / test / demo targets
  pyproject.toml       # package metadata and tool config
  fremont.mp4          # demo recording
  README.md
```
 
## Connecting to MongoDB Atlas

`--uri` (or `MONGO_URI`) accepts any valid connection string, including Atlas:

```dotenv
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=halo2_archive
```

Then every command works exactly the same as with a local instance:

```bash
fremont overview
fremont explain matches --filter '{"map":"Lockout"}' --sort '{"played_at":-1}'
```

`suggest-index` never opens a connection at all, so it works offline regardless of what `MONGO_URI` is set to.

## Testing

The test suite covers the two purely offline modules — the ESR index heuristic and the JSON parsing helpers — so no running MongoDB is required:

```bash
pytest -q
```

Tests live in `tests/test_index_advisor.py` and mirror the worked examples in this README. The intent is that if a documented example ever breaks, a test breaks with it. The MongoDB-backed commands (`overview`, `indexes`, `explain`, `benchmark`) are not covered by automated tests; use `make demo` to exercise them end-to-end against the Docker-hosted instance.

## Development

```bash
# 1. Create and activate a virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install the package and dev dependencies
make install

# 3. Lint
make lint

# 4. Run tests (no MongoDB needed)
make test

# 5. Spin up the full demo stack
make demo
```

Fremont uses [Ruff](https://docs.astral.sh/ruff/) for linting (`line-length = 100`). Run `ruff check --fix .` to apply auto-fixable suggestions before committing.

## Author
Michael Allen Mendy. (c) 2026. Named after my hometown.
