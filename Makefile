.PHONY: help build up down logs restart logs-app logs-grafana

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build all Docker images"
	@echo "  up            Start all services in detached mode"
	@echo "  down          Stop all services"
	@echo "  logs          View logs from all containers"
	@echo "  logs-app      View logs from the app service"
	@echo "  logs-grafana  View logs from the Grafana service"
	@echo "  restart       Restart all services"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app

logs-grafana:
	docker compose logs -f grafana

restart:
	docker compose down && docker compose up -d
