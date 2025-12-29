#!/bin/bash

# ============================================================================
# QUICK REFERENCE: Complete curl Examples for Table-Agnostic API
# ============================================================================
# This script provides all test cases for the production REST API

# Configuration
API_URL="http://localhost:8000"
TABLE_NAME="users"
CONTENT_TYPE="Content-Type: application/json"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Table-Agnostic REST API Testing Suite ===${NC}\n"

# ============================================================================
# 1. CREATE (INSERT) - Single Record
# ============================================================================
echo -e "${GREEN}1. CREATE - Insert a single user${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    }
  }'
EOF
echo ""

# ============================================================================
# 2. RETRIEVE - All Records (No Filter)
# ============================================================================
echo -e "${GREEN}2. RETRIEVE - Get all users${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X GET http://localhost:8000/api/users/query
EOF
echo ""

# ============================================================================
# 3. RETRIEVE - With Filter (POST)
# ============================================================================
echo -e "${GREEN}3. RETRIEVE - Get users with age = 30${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 30
    }
  }'
EOF
echo ""

# ============================================================================
# 4. RETRIEVE - Multiple Conditions
# ============================================================================
echo -e "${GREEN}4. RETRIEVE - Get users with age > 25 AND name = 'John Doe'${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 30,
      "name": "John Doe"
    }
  }'
EOF
echo ""

# ============================================================================
# 5. UPDATE - Modify Records
# ============================================================================
echo -e "${GREEN}5. UPDATE - Change user age and email where id = 1${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X PUT http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 31,
      "email": "newemail@example.com"
    },
    "where": {
      "id": 1
    }
  }'
EOF
echo ""

# ============================================================================
# 6. UPDATE - Multiple Conditions
# ============================================================================
echo -e "${GREEN}6. UPDATE - Update all users named 'John' to age 35${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X PUT http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 35
    },
    "where": {
      "name": "John Doe"
    }
  }'
EOF
echo ""

# ============================================================================
# 7. DELETE - Remove Records
# ============================================================================
echo -e "${GREEN}7. DELETE - Remove user with id = 1${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "id": 1
    }
  }'
EOF
echo ""

# ============================================================================
# 8. DELETE - Multiple Conditions
# ============================================================================
echo -e "${GREEN}8. DELETE - Remove all users older than 50${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 50
    }
  }'
EOF
echo ""

# ============================================================================
# 9. CSV IMPORT - Batch Insert
# ============================================================================
echo -e "${GREEN}9. CSV IMPORT - Bulk import users from file${NC}"
echo "Preparation:"
echo "------------"
cat << 'EOF'
# Create a test CSV file
cat > /tmp/users.csv << 'CSV'
name,email,age
Alice Johnson,alice@example.com,28
Bob Smith,bob@example.com,32
Charlie Brown,charlie@example.com,25
Diana Prince,diana@example.com,26
Eve Wilson,eve@example.com,29
CSV

# Upload the CSV (filename "users.csv" → inserts into "users" table)
curl -X POST http://localhost:8000/api/batch/import \
  -F "file=@/tmp/users.csv"
EOF
echo ""

# ============================================================================
# 10. CSV EXPORT - Download All Records
# ============================================================================
echo -e "${GREEN}10. CSV EXPORT - Download all users as CSV${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X GET http://localhost:8000/api/users/export \
  -o users_export.csv

# View the downloaded file
cat users_export.csv
EOF
echo ""

# ============================================================================
# 11. ERROR HANDLING - Non-existent Table
# ============================================================================
echo -e "${GREEN}11. ERROR - Try to query non-existent table${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/nonexistent_table \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "test"
    }
  }'

# Expected Response (404):
# {
#   "timestamp": "2025-12-29T10:30:45.123456Z",
#   "error_code": "404",
#   "message": "Table 'nonexistent_table' does not exist",
#   "retry_count": 0
# }
EOF
echo ""

# ============================================================================
# 12. ERROR HANDLING - Missing WHERE Clause (Safety Guard)
# ============================================================================
echo -e "${GREEN}12. ERROR - Try to delete without WHERE clause${NC}"
echo "Command:"
echo "--------"
cat << 'EOF'
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {}
  }'

# Expected Response (400):
# {
#   "timestamp": "2025-12-29T10:30:45.123456Z",
#   "error_code": "400",
#   "message": "Invalid operation: DELETE requires WHERE conditions for safety",
#   "retry_count": 0
# }
EOF
echo ""

# ============================================================================
# 13. RETRY BEHAVIOR - Simulate Timeout
# ============================================================================
echo -e "${GREEN}13. RESILIENCY - Example timeout with retry count${NC}"
echo "Info:"
echo "-----"
cat << 'EOF'
If a database timeout occurs, the API automatically retries:
- Attempt 0: 200ms timeout
- Attempt 1: 400ms timeout (after 400ms delay)
- Attempt 2: 800ms timeout (after 800ms delay)
- Attempt 3: 1600ms timeout (after 1600ms delay)

If all 4 attempts fail, response:
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "504",
  "message": "Database operation timed out after 4 attempts",
  "retry_count": 4
}
EOF
echo ""

# ============================================================================
# 14. DYNAMIC TABLE SUPPORT
# ============================================================================
echo -e "${GREEN}14. DYNAMIC TABLES - Works with any table${NC}"
echo "Examples:"
echo "---------"
cat << 'EOF'
# Products table
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Widget", "price": 9.99}}'

# Orders table
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"input": {"customer_id": 1, "product_id": 5, "quantity": 2}}'

# Customers table
curl -X POST http://localhost:8000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"input": {"first_name": "Jane", "last_name": "Smith"}}'

# Any table with any schema works!
EOF
echo ""

# ============================================================================
# 15. ADVANCED: Complex Filter Examples
# ============================================================================
echo -e "${GREEN}15. ADVANCED - Complex filtering examples${NC}"
echo "Note: Filters use AND logic (all conditions must match)"
echo "Command examples:"
echo "-----------------"
cat << 'EOF'
# Find users with exact name AND age
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "John Doe",
      "age": 30
    }
  }'

# Update multiple columns for a specific user
curl -X PUT http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 35,
      "email": "updated@example.com",
      "status": "active"
    },
    "where": {
      "id": 5
    }
  }'

# Delete records matching multiple conditions
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "status": "inactive",
      "age": 99
    }
  }'
EOF
echo ""

# ============================================================================
# 16. TESTING CHECKLIST
# ============================================================================
echo -e "${BLUE}=== TESTING CHECKLIST ===${NC}"
cat << 'EOF'

Prerequisites:
  [ ] MySQL server running
  [ ] Database created: CREATE DATABASE test_db;
  [ ] Test table created:
      CREATE TABLE test_db.users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        age INT
      );
  [ ] Environment variables set (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
  [ ] API server running: python main.py

Test Coverage:
  [ ] Test 1: CREATE - Insert single record
  [ ] Test 2: RETRIEVE - Get all records
  [ ] Test 3: RETRIEVE - Filter by column
  [ ] Test 4: UPDATE - Modify single record
  [ ] Test 5: UPDATE - Multiple columns
  [ ] Test 6: DELETE - Remove single record
  [ ] Test 7: CSV IMPORT - Batch insert
  [ ] Test 8: CSV EXPORT - Download CSV
  [ ] Test 9: ERROR - Non-existent table (404)
  [ ] Test 10: ERROR - Missing WHERE (400)
  [ ] Test 11: RESILIENCY - Verify retry headers
  [ ] Test 12: DYNAMIC - Test with different table

Success Criteria:
  [ ] All successful responses return HTTP 200
  [ ] All responses include timestamp, message, data, retry_count
  [ ] All errors include error_code and timestamp
  [ ] CSV import tracks inserted vs failed records
  [ ] CSV export streams without memory issues
  [ ] Safety guards prevent accidental bulk deletes/updates
  [ ] Retry counts increase on timeout scenarios

EOF

echo -e "${BLUE}=== END OF QUICK REFERENCE ===${NC}"
