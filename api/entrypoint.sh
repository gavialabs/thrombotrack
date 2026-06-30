#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting Flask Application ===${NC}"

# ---------- Set DATABASE_URL ----------

## Encode to URL safe password
## AWS secretsmanager avoids some common charac that breaks DB connections
## TODO: Check if this is a fair assumption that AWS secretsmanager generated pass is safe and does not need URL-safe encoding
# ENCODED_PASS=$(python - << 'PYEOF'
# import urllib.parse, os
# print(urllib.parse.quote(os.environ["DB_PASS"]))
# PYEOF
# )
# export DATABASE_URL="postgresql://${DB_USER}:${ENCODED_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

## Assuming that the password is URL safe
# export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# # ---------- Verify that DATABASE_URL is defined ----------
# if [ -z "$DATABASE_URL" ]; then
#   echo -e "${RED}✗ Error: DATABASE_URL is not defined${NC}"
#   exit 1
# fi

# ---------- Set PYTHONPATH ----------
export PYTHONPATH=/app:$PYTHONPATH

# # ---------- Wait for database to be ready ----------
# echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
# MAX_TRIES=30
# TRIES=0

# # until psql "$DATABASE_URL" -c '\l' > /dev/null 2>&1; do
# until psql "$DATABASE_URL" -c '\l'; do
#   TRIES=$((TRIES+1))
#   if [ $TRIES -eq $MAX_TRIES ]; then
#     echo -e "${RED}✗ Timeout: unable to connect to database${NC}"
#     exit 1
#   fi
#   echo -e "${YELLOW}  Attempt $TRIES/$MAX_TRIES...${NC}"
#   sleep 2
# done

# echo -e "${GREEN}✓ Database ready${NC}"

# ---------- Run Alembic migrations ----------
echo -e "${GREEN}📦 Applying database migrations...${NC}"
if alembic upgrade head; then
  echo -e "${GREEN}✓ Migrations applied successfully${NC}"
else
  echo -e "${RED}✗ Error applying migrations${NC}"
  exit 1
fi

# ---------- Start Flask application ----------
echo -e "${GREEN}🚀 Starting Flask server on local port ${API_PORT:-5000}:5000${NC}"
# Flask will run on port 5000 within the container, but is accessible through API_PORT
# exec python -m flask run --host=0.0.0.0 --port=5000 --debug
exec gunicorn --config gunicorn_config.py app:app