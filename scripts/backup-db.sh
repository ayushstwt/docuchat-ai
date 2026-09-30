#!/usr/bin/env bash
# Usage: ./scripts/backup-db.sh <staging|prod>   (cron से रोज़ चलाएँ)
set -euo pipefail
ENV="${1:?usage: scripts/backup-db.sh <staging|prod>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/backups"; mkdir -p "$OUT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

"$ROOT/scripts/compose.sh" "$ENV" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$OUT/docuchat-$ENV-$STAMP.dump"

find "$OUT" -name "docuchat-$ENV-*.dump" -mtime +14 -delete   # 14 दिन से पुराने हटाओ
echo "Backup saved: $OUT/docuchat-$ENV-$STAMP.dump"
