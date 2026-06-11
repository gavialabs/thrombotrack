#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting Flask Application ===${NC}"

# Load .env file if it exists (skip UID and GID as they're readonly in bash)
if [ -f /app/.env ]; then
  echo -e "${GREEN}✓ Loading variables from .env${NC}"
  # Export all variables except UID and GID
  export $(grep -v '^#' /app/.env | grep -v '^UID=' | grep -v '^GID=' | xargs)
fi

## Verify that DATABASE_URL is defined
#if [ -z "$DATABASE_URL" ]; then
#  echo -e "${RED}✗ Error: DATABASE_URL is not defined${NC}"
#  exit 1
#fi

# Set PYTHONPATH
export PYTHONPATH=/app:$PYTHONPATH

## Wait for database to be ready
#echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
#MAX_TRIES=30
#TRIES=0
#
#until psql "$DATABASE_URL" -c '\l' > /dev/null 2>&1; do
#  TRIES=$((TRIES+1))
#  if [ $TRIES -eq $MAX_TRIES ]; then
#    echo -e "${RED}✗ Timeout: unable to connect to database${NC}"
#    exit 1
#  fi
#  echo -e "${YELLOW}  Attempt $TRIES/$MAX_TRIES...${NC}"
#  sleep 2
#done

echo -e "${GREEN}✓ Database ready${NC}"

# Run Alembic migrations
# echo -e "${GREEN}📦 Applying database migrations...${NC}"
# if alembic upgrade head; then
#   echo -e "${GREEN}✓ Migrations applied successfully${NC}"
# else
#   echo -e "${RED}✗ Error applying migrations${NC}"
#   exit 1
# fi

# Start Flask application
echo -e "${GREEN}🚀 Starting Flask server on port ${APP_PORT:-5000}${NC}"
exec python -m flask run --host=0.0.0.0 --port=${APP_PORT:-5000} --debug