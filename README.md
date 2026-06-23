# Fremont

https://github.com/user-attachments/assets/f209c0d7-ac4d-4ddf-bd20-3de8afc172ed

Fremont is a remix of a MongoDB performance helper CLI demo built for HaloArchives.com

Fremont helps you inspect MongoDB collections, run query explain plans, benchmark query shapes, and suggest basic compound indexes. So for example:

- `players`
- `matches`
- `player_stats`
- `playlists`

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

## Seed the Halo 2 demo database

```bash
python scripts_seed_halo2.py
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
┣━━━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━┫
┃ matches      ┃  50,000   ┃    5    ┃
┃ players      ┃   5,000   ┃    4    ┃
┃ player_stats ┃ 200,000   ┃    6    ┃
┃ playlists    ┃      10   ┃    2    ┃
┗━━━━━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━┛
```

## Example explain command

```bash
fremont explain matches \
  --db halo2_archive \
  --filter '{"map":"Lockout","playlist":"MLG"}' \
  --sort '{"played_at":-1}' \
  --limit 5
```

## Example benchmark command

```bash
fremont benchmark player_stats \
  --db halo2_archive \
  --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
  --sort '{"kills":-1}' \
  --limit 10 \
  --runs 50
```

## Example index suggestion

```bash
fremont suggest-index player_stats \
  --filter '{"gamertag":"Crafty Kisses","playlist":"MLG"}' \
  --sort '{"played_at":-1}'
```

Output:

```js
db.player_stats.createIndex({ "gamertag": 1, "playlist": 1, "played_at": -1 })
```

## Repo layout

```text
fremont/
  src/fremont/
    analyzer.py
    cli.py
    config.py
    index_advisor.py
    json_tools.py
    mongo_client.py
    reporting.py
  tests/
  examples/
  media/
  scripts_seed_halo2.py
  docker-compose.yml
  pyproject.toml
  README.md
```
