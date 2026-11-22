#!/usr/bin/env bash
# Compare Codex generate-json-schema output with the adapter contract.
# Without CODEX_BIN / CODEX_SCHEMA_DIR this only runs Go tests and must not fail CI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> adapter contract unit tests"
go test ./internal/engine/codex -count=1 -timeout=60s -run 'TestAdapterContract'

SCHEMA_DIR="${CODEX_SCHEMA_DIR:-}"
if [[ -z "${SCHEMA_DIR}" && -n "${CODEX_BIN:-}" ]]; then
  if [[ ! -x "${CODEX_BIN}" ]]; then
    echo "CODEX_BIN is set but not executable (${CODEX_BIN}); skipping generated schema compare"
    exit 0
  fi
  SCHEMA_DIR="$(mktemp -d)"
  cleanup() { rm -rf "${SCHEMA_DIR}"; }
  trap cleanup EXIT
  echo "==> generate-json-schema via ${CODEX_BIN}"
  if ! "${CODEX_BIN}" app-server generate-json-schema --out "${SCHEMA_DIR}"; then
    echo "generate-json-schema unavailable; skipping generated schema compare"
    exit 0
  fi
fi

if [[ -z "${SCHEMA_DIR}" ]]; then
  echo "CODEX_SCHEMA_DIR/CODEX_BIN unset; unit tests are the CI gate"
  exit 0
fi

echo "==> compare generated schema at ${SCHEMA_DIR}"
CODEX_SCHEMA_DIR="${SCHEMA_DIR}" go test ./internal/engine/codex -count=1 -timeout=60s -run TestCompareGeneratedSchemaIfPresent
