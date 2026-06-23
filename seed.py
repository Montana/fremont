from __future__ import annotations

from datetime import datetime, timedelta
import random

from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "halo2_archive"

random.seed(117)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

for collection_name in ["players", "matches", "player_stats", "playlists"]:
    db[collection_name].drop()

maps = [
    "Lockout",
    "Midship",
    "Warlock",
    "Beaver Creek",
    "Sanctuary",
    "Ivory Tower",
    "Turf",
    "Colossus",
]

playlists = [
    {"name": "MLG", "mode": "competitive", "team_size": 4},
    {"name": "Team Slayer", "mode": "ranked", "team_size": 4},
    {"name": "Double Team", "mode": "ranked", "team_size": 2},
    {"name": "Rumble Pit", "mode": "ranked", "team_size": 1},
]

db.playlists.insert_many(playlists)
db.playlists.create_index("name", unique=True)

base_gamertags = [
    "Crafty Kisses",
    "StrongSide",
    "Walshy",
    "Karma",
    "Ogre 1",
    "Ogre 2",
    "Dysphoria",
    "Konishiwa",
    "Latrine Marine",
    "Donut650",
    "GeXnY",
    "gporter",
]

players = []
for i in range(5000):
    if i < len(base_gamertags):
        gamertag = base_gamertags[i]
    else:
        gamertag = f"Player{i:05d}"

    players.append(
        {
            "gamertag": gamertag,
            "region": random.choice(["West", "East", "Midwest", "South", "EU"]),
            "joined_at": datetime.utcnow() - timedelta(days=random.randint(100, 7000)),
            "highest_level": random.randint(1, 50),
        }
    )

db.players.insert_many(players)
db.players.create_index("gamertag", unique=True)
db.players.create_index([("region", 1), ("highest_level", -1)])

matches = []
for i in range(50000):
    matches.append(
        {
            "match_id": f"match_{i:08d}",
            "map": random.choice(maps),
            "playlist": random.choice([p["name"] for p in playlists]),
            "duration_seconds": random.randint(330, 900),
            "played_at": datetime.utcnow() - timedelta(days=random.randint(1, 4200)),
            "winner_team": random.choice(["red", "blue"]),
        }
    )

db.matches.insert_many(matches)
db.matches.create_index("match_id", unique=True)
db.matches.create_index([("map", 1), ("playlist", 1), ("played_at", -1)])
db.matches.create_index([("playlist", 1), ("winner_team", 1)])

stats = []
for i in range(200000):
    gamertag = random.choice(base_gamertags if random.random() < 0.08 else [f"Player{random.randint(12, 4999):05d}"])
    kills = random.randint(1, 50)
    deaths = random.randint(1, 45)
    assists = random.randint(0, 25)

    stats.append(
        {
            "stat_id": f"stat_{i:09d}",
            "match_id": f"match_{random.randint(0, 49999):08d}",
            "gamertag": gamertag,
            "playlist": random.choice([p["name"] for p in playlists]),
            "map": random.choice(maps),
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "kd_ratio": round(kills / max(deaths, 1), 2),
            "played_at": datetime.utcnow() - timedelta(days=random.randint(1, 4200)),
        }
    )

db.player_stats.insert_many(stats)
db.player_stats.create_index("stat_id", unique=True)
db.player_stats.create_index([("gamertag", 1), ("playlist", 1), ("played_at", -1)])
db.player_stats.create_index([("gamertag", 1), ("playlist", 1), ("kills", -1)])
db.player_stats.create_index([("map", 1), ("playlist", 1)])
db.player_stats.create_index([("kd_ratio", -1)])

print("Seeded halo2_archive.")
print("")
print("Try:")
print("fremont overview --db halo2_archive")
print("fremont explain matches --db halo2_archive --filter '{\"map\":\"Lockout\",\"playlist\":\"MLG\"}' --sort '{\"played_at\":-1}' --limit 5")
print("fremont benchmark player_stats --db halo2_archive --filter '{\"gamertag\":\"Crafty Kisses\",\"playlist\":\"MLG\"}' --sort '{\"kills\":-1}' --limit 10 --runs 50")
