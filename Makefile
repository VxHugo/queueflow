.PHONY: up down test lint build demo

up:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .

build:
	docker compose build

demo: up

