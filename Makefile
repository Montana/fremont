install:
	pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest -q

demo-up:
	docker compose up -d

demo-seed:
	python seed.py

demo:
	docker compose up -d
	python seed.py
	fremont overview --db halo2_archive
