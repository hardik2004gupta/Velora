#!/usr/bin/env bash
# Generate the initial Alembic migration from ORM models.
# Run once after Phase 1 scaffold is complete.
#
# Usage:
#   ./scripts/create_initial_migration.sh

set -euo pipefail

echo "Generating initial migration..."
poetry run alembic revision --autogenerate -m "create_initial_tables"
echo "Done. Review the generated file in alembic/versions/ before applying."
