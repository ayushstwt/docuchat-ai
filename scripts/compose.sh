#!/usr/bin/env bash
# Usage: ./scripts/compose.sh <dev|staging|prod> <docker compose arguments...>
set -euo pipefail

ENV="${1:?usage: scripts/compose.sh <dev|staging|prod> <docker compose args...>}"
shift
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "$ENV" in
  dev|staging|prod) ;;
  *) echo "Unknown environment: $ENV (use dev, staging or prod)" >&2; exit 1 ;;
esac

[[ -f "$ROOT/deploy/env/$ENV.env" ]] || { echo "Missing deploy/env/$ENV.env (copy from $ENV.env.example)" >&2; exit 1; }

PROFILE=()
[[ "$ENV" != "dev" ]] && PROFILE=(--profile edge)

exec docker compose \
  --env-file "$ROOT/deploy/env/$ENV.env" \
  ${PROFILE[@]+"${PROFILE[@]}"} \
  -f "$ROOT/deploy/docker-compose.yml" \
  -f "$ROOT/deploy/docker-compose.$ENV.yml" \
  "$@"
