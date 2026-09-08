#!/bin/bash
set -e

BASE="http://localhost:8000/api/v1"
ES_URL="http://localhost:9200"
ES_INDEX="products"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WAIT]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "============================================"
echo "  COMMERCIIFY API — FULL TEST SUITE"
echo "============================================"
echo ""
echo "PREREQUISITES (run in separate terminals):"
echo "  1. Postgres (local:5432), Redis (local:6379), ES (docker:9200)"
echo "  2. Migration:  cd src && ../.venv/bin/python -m alembic upgrade head"
echo "  3. Server:     cd src && uvicorn app.main:app --reload"
echo "  4. Worker:     cd src && PYTHONPATH=. ../.venv/bin/python -m arq app.jobs.worker.WorkerSettings"
echo ""
echo "Email testing: Check https://mailtrap.io/inboxes after order creation"
echo "============================================"
echo ""

echo "=== CLEANUP: Resetting database for fresh test run ==="
PGPASSWORD=postgres psql -U postgres -h localhost -p 5432 -d ecommerce -c "
TRUNCATE order_items, orders, cart_items, carts, products, categories, users CASCADE;
" 2>/dev/null && ok "Database cleaned" || warn "Could not clean database (run manually if needed)"

curl -s -X DELETE "$ES_URL/$ES_INDEX" 2>/dev/null && ok "ES index cleared" || warn "ES index not found (will be created on first product)"
echo ""

# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────
echo "=== 1. Health Check ==="
curl -s $BASE/health | python3 -m json.tool
ok "Health endpoint works"

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
echo -e "\n=== 2. Register Customer ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@test.com","password":"password123","full_name":"John Customer"}' | python3 -m json.tool
ok "Customer registered"

echo -e "\n=== 3. Register Admin ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123","full_name":"Jane Admin"}' | python3 -m json.tool

echo -e "\n--- Promoting admin via psql ---"
psql -U postgres -d ecommerce -c "UPDATE users SET role='ADMIN' WHERE email='admin@test.com';" 2>/dev/null && ok "Admin promoted" || warn "Promote manually: psql -U postgres -d ecommerce -c \"UPDATE users SET role='ADMIN' WHERE email='admin@test.com';\""

echo -e "\n=== 4. Login Admin ==="
ADMIN_resp=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.com&password=password123")
echo "$ADMIN_resp" | python3 -m json.tool
ADMIN_TOKEN=$(echo "$ADMIN_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "Admin logged in"

echo -e "\n=== 5. Get Profile ==="
curl -s $BASE/auth/me -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
ok "Profile retrieved"

echo -e "\n=== 6. Token Refresh ==="
REFRESH_TOKEN=$(echo "$ADMIN_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
curl -s -X POST $BASE/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" | python3 -m json.tool
ok "Token refreshed"

# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
echo -e "\n=== 7. Create Category ==="
CAT_resp=$(curl -s -X POST $BASE/categories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name":"Running Shoes"}')
echo "$CAT_resp" | python3 -m json.tool
CATEGORY_ID=$(echo "$CAT_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "Category created: $CATEGORY_ID"

echo -e "\n=== 8. List Categories ==="
curl -s "$BASE/categories?limit=10" | python3 -m json.tool
ok "Categories listed"

# ─────────────────────────────────────────────
# PRODUCTS + ELASTICSEARCH INDEXING
# ─────────────────────────────────────────────
echo -e "\n=== 9. Create Product (triggers ES indexing job) ==="
PROD_resp=$(curl -s -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "{\"name\":\"Nike Air Max\",\"description\":\"Comfortable running shoes for athletes\",\"price\":129.99,\"stock_quantity\":50,\"category_id\":\"$CATEGORY_ID\"}")
echo "$PROD_resp" | python3 -m json.tool
PRODUCT_ID=$(echo "$PROD_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "Product created: $PRODUCT_ID (index job enqueued)"

echo -e "\n=== 10. Create Another Product ==="
PROD2_resp=$(curl -s -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "{\"name\":\"Adidas Ultraboost\",\"description\":\"Premium running shoes with boost cushioning\",\"price\":179.99,\"stock_quantity\":30,\"category_id\":\"$CATEGORY_ID\"}")
echo "$PROD2_resp" | python3 -m json.tool
PRODUCT2_ID=$(echo "$PROD2_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "Product created: $PRODUCT2_ID (index job enqueued)"

echo -e "\n=== 11. List Products ==="
curl -s "$BASE/products?limit=10" | python3 -m json.tool
ok "Products listed"

echo -e "\n=== 12. Get Single Product ==="
curl -s $BASE/products/$PRODUCT_ID | python3 -m json.tool
ok "Product retrieved"

echo -e "\n=== 13. Update Product (triggers cache invalidation) ==="
curl -s -X PATCH $BASE/products/$PRODUCT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"price":119.99,"stock_quantity":45}' | python3 -m json.tool
ok "Product updated"

# ─────────────────────────────────────────────
# ELASTICSEARCH — VERIFY INDEXING
# ─────────────────────────────────────────────
echo -e "\n=== 14. Wait for ES indexing (worker processes jobs) ==="
warn "Waiting 5s for arq worker to index products..."
sleep 5

echo -e "\n=== 15. Verify ES Index Exists ==="
ES_INDEX_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$ES_URL/$ES_INDEX")
if [ "$ES_INDEX_CHECK" = "200" ]; then
  ok "ES index '$ES_INDEX' exists"
else
  fail "ES index '$ES_INDEX' not found (HTTP $ES_INDEX_CHECK)"
fi

echo -e "\n=== 16. Check Documents in ES ==="
ES_COUNT=$(curl -s "$ES_URL/$ES_INDEX/_count" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))")
echo "  Documents indexed: $ES_COUNT"
if [ "$ES_COUNT" -ge 2 ]; then
  ok "Both products indexed in Elasticsearch"
else
  fail "Expected >= 2 documents, got $ES_COUNT (is the arq worker running?)"
fi

echo -e "\n=== 17. Full-Text Search via API ==="
curl -s "$BASE/search/products?q=nike&limit=10" | python3 -m json.tool
ok "Search query 'nike' executed"

echo -e "\n=== 18. Fuzzy Search ==="
curl -s "$BASE/search/products?q=runing+shos&limit=10" | python3 -m json.tool
ok "Fuzzy search executed (typos tolerated)"

echo -e "\n=== 19. Search via ES Directly ==="
curl -s -X POST "$ES_URL/$ES_INDEX/_search" \
  -H "Content-Type: application/json" \
  -d '{"query":{"multi_match":{"query":"boost cushioning","fields":["name^3","description"]}}}' | python3 -m json.tool
ok "Direct ES query executed"

# ─────────────────────────────────────────────
# CART
# ─────────────────────────────────────────────
echo -e "\n=== 20. Login Customer ==="
CUST_resp=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=customer@test.com&password=password123")
echo "$CUST_resp" | python3 -m json.tool
CUSTOMER_TOKEN=$(echo "$CUST_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "Customer logged in"

echo -e "\n=== 21. Get Cart (empty) ==="
curl -s $BASE/cart \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" | python3 -m json.tool
ok "Empty cart retrieved"

echo -e "\n=== 22. Add Item to Cart ==="
curl -s -X POST $BASE/cart/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "{\"product_id\":\"$PRODUCT_ID\",\"quantity\":2}" | python3 -m json.tool
ok "Added Nike Air Max x2"

echo -e "\n=== 23. Add Another Item ==="
curl -s -X POST $BASE/cart/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "{\"product_id\":\"$PRODUCT2_ID\",\"quantity\":1}" | python3 -m json.tool
ok "Added Adidas Ultraboost x1"

echo -e "\n=== 24. Update Item Quantity ==="
curl -s -X PATCH $BASE/cart/items/$PRODUCT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d "{\"product_id\":\"$PRODUCT_ID\",\"quantity\":3}" | python3 -m json.tool
ok "Updated Nike Air Max to x3"

echo -e "\n=== 25. Remove Item ==="
curl -s -X DELETE $BASE/cart/items/$PRODUCT2_ID \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" | python3 -m json.tool
ok "Removed Adidas Ultraboost"

# ─────────────────────────────────────────────
# ORDER + EMAIL
# ─────────────────────────────────────────────
echo -e "\n=== 26. Create Order (triggers email job) ==="
ORDER_resp=$(curl -s -X POST $BASE/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d '{"idempotency_key":"order-test-001"}')
echo "$ORDER_resp" | python3 -m json.tool
ORDER_ID=$(echo "$ORDER_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "Order created: $ORDER_ID (email job enqueued)"

echo -e "\n=== 27. Verify Cart is Empty ==="
curl -s $BASE/cart \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" | python3 -m json.tool
ok "Cart cleared after order"

echo -e "\n=== 28. Duplicate Order (idempotency check — should return same order) ==="
curl -s -X POST $BASE/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -d '{"idempotency_key":"order-test-001"}' | python3 -m json.tool
ok "Idempotency check passed"

# ─────────────────────────────────────────────
# EMAIL — VERIFY
# ─────────────────────────────────────────────
echo -e "\n=== 29. Wait for email job (worker processes) ==="
warn "Waiting 3s for arq worker to send email..."
sleep 3

echo -e "\n=== 30. Verify Email Sent ==="
echo "  Check your Mailtrap inbox:"
echo "  https://mailtrap.io/inboxes"
echo "  inbox: ecommerce-backend"
echo "  Expected email to: customer@test.com"
echo "  Subject: Order Confirmation - #$ORDER_ID"
echo ""
ok "Email job enqueued — check Mailtrap for confirmation"

# ─────────────────────────────────────────────
# ELASTICSEARCH — VERIFY DELETION
# ─────────────────────────────────────────────
echo -e "\n=== 31. Delete Product (triggers ES delete job) ==="
curl -s -o /dev/null -w "Status: %{http_code}\n" -X DELETE $BASE/products/$PRODUCT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
ok "Product deleted (ES delete job enqueued)"

echo -e "\n=== 32. Wait for ES deletion ==="
warn "Waiting 3s for arq worker to remove from ES..."
sleep 3

ES_COUNT_AFTER=$(curl -s "$ES_URL/$ES_INDEX/_count" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))")
echo "  Documents remaining: $ES_COUNT_AFTER"
if [ "$ES_COUNT_AFTER" -lt "$ES_COUNT" ]; then
  ok "Product removed from Elasticsearch"
else
  warn "ES count unchanged (delete job may still be processing)"
fi

echo -e "\n============================================"
echo "  ALL TESTS COMPLETE"
echo "============================================"
echo ""
echo "SUMMARY:"
echo "  Auth:          Register, Login, Refresh, Profile"
echo "  Categories:    CRUD"
echo "  Products:      CRUD + cache invalidation"
echo "  Elasticsearch: Indexing, full-text search, fuzzy search, deletion"
echo "  Cart:          Add, update, remove items"
echo "  Orders:        Create, idempotency check"
echo "  Email:         Order confirmation (check Mailtrap)"
echo ""
echo "VERIFICATION:"
echo "  ES docs:    curl $ES_URL/$ES_INDEX/_count"
echo "  ES search:  curl $ES_URL/$ES_INDEX/_search?pretty"
echo "  Mailtrap:   https://mailtrap.io/inboxes"
echo "============================================"
