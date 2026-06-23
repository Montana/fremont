install:
	pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest -q

demo-up:
	docker compose up -d

demo-seed:
	python scripts_seed_halo2.py

demo:
	docker compose up -d
	python scripts_seed_halo2.py
	fremont overview --db halo2_archive
