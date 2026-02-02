#!/bin/sh
# Check license eligibility via Admin API (requires admin auth).
# Usage: ./check_license_via_api.sh <email> [discipline]
# Example: ./check_license_via_api.sh vasilevigor3@gmail.com gt
# You must be logged in as admin in the app and pass the session cookie, or use a token.
# Alternative: run the DB script instead (no auth):
#   docker compose exec app python backend/scripts/check_license_eligibility.py vasilevigor3@gmail.com gt

EMAIL="${1:?Usage: $0 <email> [discipline]}"
DISCIPLINE="${2:-gt}"
BASE="${BASE_URL:-http://localhost:8001}"

echo "GET $BASE/api/admin/license-award-check?email=$EMAIL&discipline=$DISCIPLINE"
echo " (requires admin session cookie or token)"
curl -s -H "Cookie: ${COOKIE:-}" "$BASE/api/admin/license-award-check?email=$(echo "$EMAIL" | sed 's/@/%40/g')&discipline=$DISCIPLINE" | python3 -m json.tool
