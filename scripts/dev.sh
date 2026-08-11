#!/usr/bin/env bash
# Local dev loop. `vercel dev` serves index.html and /api on one origin, which is the
# only way to reproduce production routing (and to avoid inventing a CORS problem that
# does not exist in production).
set -euo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] || { echo "no .env — cp .env.example .env first"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements-dev.txt

python scripts/ingest_kb.py

if command -v vercel >/dev/null 2>&1; then
  vercel dev
else
  echo "vercel CLI not found — serving the page only (no /api)"
  python3 -m http.server 3000
fi
