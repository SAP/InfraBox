COMPOSE = DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
  docker compose -f $(CURDIR)/docker-compose.yml
ROOT = $(CURDIR)/../..

.PHONY: start stop logs frontend

start:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example — edit the password before retrying."; exit 1; fi
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

frontend:
	cd $(ROOT)/src/dashboard-client && \
	  npm install --legacy-peer-deps --ignore-scripts && \
	  npm run dev
