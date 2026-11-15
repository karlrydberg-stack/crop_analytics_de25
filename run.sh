#!/usr/bin/env bash
# =====================================================================
# Short commands for the crop_analytics_de25 project.
# Usage (Git Bash, from anywhere in the repo):   ./run.sh <command>
# Run  ./run.sh  with no command to see the list.
# =====================================================================
set -e
cd "$(dirname "$0")"   # always work from the repo root

#ASSETS="raw_crops,cleaned_crops,warehouse_models,warehouse_tests"
ASSETS="database_setup,raw_crops,cleaned_crops,warehouse_models,warehouse_tests"

case "$1" in

  # --- Local database (crop_db) ---------------------------------------
  db)
    docker compose --profile local-db up -d db
    docker ps --filter name=crop_db
    ;;
  db-stop)
    docker compose --profile local-db stop db
    ;;
  db-reset)
    read -p "This deletes ALL local data. Continue? (y/n) " answer
    [ "$answer" = "y" ] && docker compose --profile local-db down -v
    ;;
  psql)
    # Git Bash on Windows needs winpty for interactive programs
    if command -v winpty >/dev/null 2>&1; then
      winpty docker exec -it crop_db psql -U cropadmin -d crops
    else
      docker exec -it crop_db psql -U cropadmin -d crops
    fi
    ;;

  # --- Pipeline (CSV -> staging -> cleaned -> warehouse) --------------
  pipeline)
    uv run --env-file .env dagster asset materialize --select "$ASSETS" \
      -m backend.orchestration.definitions
    ;;
  dagster)
    uv run --env-file .env dagster dev -m backend.orchestration.definitions
    ;;

  # --- dbt (default: build; or e.g.  ./run.sh dbt debug) --------------
  dbt)
    shift
    cd backend/dbt
    DBT_PROFILES_DIR=../docker/dbt uv run --env-file ../../.env dbt "${@:-build}"
    ;;

  # --- Streamlit -------------------------------------------------------
  app)
    uv run --env-file .env streamlit run frontend/app.py
    ;;

  # --- Docker: the whole stack ----------------------------------------
  up)
    docker compose --profile local-db up -d --build
    docker ps
    ;;
  down)
    docker compose --profile local-db down
    ;;
  logs)
    docker compose logs -f "${2:-backend}"
    ;;

  # --- Help -------------------------------------------------------------
  *)
    cat <<'EOF'
Usage: ./run.sh <command>

Database
  db          start the local database (crop_db)
  db-stop     stop it (data is kept)
  db-reset    delete all local data (asks first)
  psql        open psql in crop_db

Pipeline
  pipeline    run the whole pipeline once (CSV -> warehouse)
  dagster     open the Dagster UI on http://localhost:3000

dbt
  dbt         dbt build (seeds + models + tests)
  dbt debug   any dbt command, e.g. debug, parse, run, test

Streamlit
  app         start Streamlit on http://localhost:8501

Docker (everything)
  up          build and start db + backend + frontend
  down        stop everything (data is kept)
  logs        follow backend logs  (./run.sh logs frontend for the frontend)
EOF
    ;;
esac