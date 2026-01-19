#!/usr/bin/env bash
set -euo pipefail

required=(psql pg_dump pg_restore python3)
optional=(diff)

missing=()

echo "Required:"
for cmd in "${required[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ok   $cmd"
  else
    echo "  missing $cmd"
    missing+=("$cmd")
  fi
done

echo ""
echo "Optional:"
for cmd in "${optional[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ok   $cmd"
  else
    echo "  missing $cmd"
  fi
done

if (( ${#missing[@]} == 0 )); then
  exit 0
fi

echo ""
echo "Install hints:"
case "$(uname -s 2>/dev/null || echo unknown)" in
  Darwin)
    echo "  macOS: brew install postgresql"
    ;;
  Linux)
    echo "  Ubuntu/Debian: sudo apt install -y postgresql-client"
    echo "  Fedora: sudo dnf install -y postgresql"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "  Windows: winget install PostgreSQL.PostgreSQL"
    echo "  Windows (diff): install Git or diffutils for diff.exe"
    ;;
  *)
    echo "  Install PostgreSQL client tools for psql/pg_dump/pg_restore."
    ;;
esac

exit 1
