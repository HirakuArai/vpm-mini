compose-build:
	@if [ -f compose.yaml ]; then \
		docker compose build; \
	else \
		echo "compose.yaml not found; will be added in S2. Skipping build."; \
	fi

compose-up:
	docker compose up -d --wait

compose-down:
	docker compose down -v

compose-logs:
	docker compose logs --no-color --tail=200