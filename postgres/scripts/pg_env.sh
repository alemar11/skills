#!/usr/bin/env bash

if [[ -z "${PGAPPNAME:-}" ]]; then
  export PGAPPNAME="${DB_APPLICATION_NAME:-codex-postgres-skill}"
fi

if ! command -v psql >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    formula="$(brew list --versions 2>/dev/null | awk '/^postgresql(@[0-9]+)? / {print $1}' | sort -V | tail -n 1)"
    if [[ -n "$formula" ]]; then
      prefix="$(brew --prefix "$formula" 2>/dev/null || true)"
      if [[ -n "$prefix" && -d "$prefix/bin" ]]; then
        export PATH="$prefix/bin:$PATH"
      fi
    fi
  fi
fi

if [[ -n "${DB_STATEMENT_TIMEOUT_MS:-}" || -n "${DB_LOCK_TIMEOUT_MS:-}" ]]; then
  pgopts="${PGOPTIONS:-}"
  if [[ -n "${DB_STATEMENT_TIMEOUT_MS:-}" ]]; then
    pgopts="${pgopts} -c statement_timeout=${DB_STATEMENT_TIMEOUT_MS}"
  fi
  if [[ -n "${DB_LOCK_TIMEOUT_MS:-}" ]]; then
    pgopts="${pgopts} -c lock_timeout=${DB_LOCK_TIMEOUT_MS}"
  fi
  export PGOPTIONS="$pgopts"
fi
