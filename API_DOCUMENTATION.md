# Production-Ready REST API: Table-Agnostic CRUD with Resiliency

## Overview

This is a complete, modular FastAPI backend implementation that provides:

1. **Dynamic CRUD Interface**: Table-agnostic endpoints for any database table
2. **Resiliency Engine**: Custom retry logic with exponential backoff
3. **CSV Automation**: Batch import/export with streaming support
4. **Safety Guardrails**: SQL injection prevention, parameterized queries, schema validation

---

## Directory Structure

```
/Users/larrylo/SourceCode/python_mysql_http/
├── app/                              # Application package
│   ├── __init__.py
│   ├── core/                         # Core business logic
│   │   ├── __init__.py
│   │   ├── resiliency.py            # Retry wrapper with exponential backoff
│   │   └── database.py               # Query execution, table validation
│   ├── utils/                        # Utilities
│   │   ├── __init__.py
│   │   └── error_handler.py          # Standardized error/success responses
│   ├── services/                     # Business services
│   │   ├── __init__.py
│   │   └── csv_service.py            # CSV import/export logic
│   ├── routes/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── crud.py                   # Dynamic CRUD endpoints
│   │   └── csv_routes.py             # CSV import/export routes
│   └── schemas/                      # Pydantic models
│       ├── __init__.py
│       └── requests.py               # Request schemas
├── main.py                           # FastAPI application entry point
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Docker configuration
├── README.md
└── demo_data/
    └── homepage.json
```

---

## Core Components

### 1. Resiliency Engine (`app/core/resiliency.py`)

**Purpose**: Wrap all database operations with automatic retry logic and timeout handling.

**Backoff Schedule**:
- **Attempt 0** (Initial): 200ms timeout, 0ms delay
- **Attempt 1** (Retry 1): 400ms timeout, 400ms delay before
- **Attempt 2** (Retry 2): 800ms timeout, 800ms delay before
- **Attempt 3** (Retry 3): 1600ms timeout, 1600ms delay before

**Usage**:
```python
from app.core.resiliency import execute_with_retries, GatewayTimeoutException

try:
    result = await execute_with_retries(execute_insert, pool, table_name, data)
except GatewayTimeoutException as e:
    # Handle 504 Gateway Timeout
    print(f"Failed after {e.retry_count} retries: {e.message}")
```

### 2. Database Utility (`app/core/database.py`)

**Features**:
- Parameterized queries to prevent SQL injection
- Table existence validation via `INFORMATION_SCHEMA`
- Dynamic column discovery
- Supports: INSERT, SELECT, UPDATE, DELETE

**Functions**:
- `table_exists(pool, table_name, db_name)` → bool
- `get_table_columns(pool, table_name, db_name)` → List[str]
- `execute_insert(pool, table_name, data)` → rows_affected
- `execute_select(pool, table_name, where_dict)` → List[Dict]
- `execute_update(pool, table_name, data, where_dict)` → rows_affected
- `execute_delete(pool, table_name, where_dict)` → rows_affected

### 3. Error Handler (`app/utils/error_handler.py`)

**Response Format** (Standardized):
```json
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "504",
  "message": "Database operation timed out after 4 attempts",
  "retry_count": 4,
  "details": null
}
```

### 4. CSV Service (`app/services/csv_service.py`)

- **Import**: Parses CSV, uses filename as table name, batch inserts with error tracking
- **Export**: Streams CSV to prevent memory overflow on large datasets
- Handles file encoding, validation, and transaction management

---

## API Endpoints

### CRUD Operations

#### 1. CREATE: `POST /api/{tableName}`
Insert a single record.

**Request**:
```json
{
  "input": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }
}
```

**Response** (Success):
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "message": "Record inserted successfully",
  "data": {
    "rows_affected": 1
  },
  "retry_count": 0
}
```

**Response** (Failure - 504):
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "error_code": "504",
  "message": "Insert operation timed out",
  "retry_count": 4
}
```

---

#### 2. RETRIEVE: `GET /api/{tableName}/query`
Fetch all records (no filtering).

**Response**:
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "message": "Retrieved 5 record(s)",
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    },
    ...
  ],
  "retry_count": 0
}
```

---

#### 3. RETRIEVE with Filter: `POST /api/{tableName}/query`
Fetch records matching WHERE conditions.

**Request**:
```json
{
  "input": {
    "age": 30,
    "name": "John Doe"
  }
}
```

**Response**: Same as above, filtered records.

---

#### 4. UPDATE: `PUT /api/{tableName}`
Update records matching conditions.

**Request**:
```json
{
  "input": {
    "age": 31,
    "email": "newemail@example.com"
  },
  "where": {
    "id": 1
  }
}
```

**Response**:
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "message": "Record updated successfully",
  "data": {
    "rows_affected": 1
  },
  "retry_count": 0
}
```

---

#### 5. DELETE: `DELETE /api/{tableName}`
Delete records matching conditions.

**Request**:
```json
{
  "input": {
    "id": 1
  }
}
```

**Response**:
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "message": "Record deleted successfully",
  "data": {
    "rows_affected": 1
  },
  "retry_count": 0
}
```

---

### CSV Operations

#### 6. CSV IMPORT: `POST /api/batch/import`
Batch import CSV file (uses filename as table name).

**Request**:
- Content-Type: `multipart/form-data`
- File: CSV file (e.g., `users.csv` → inserts into `users` table)

**Response**:
```json
{
  "timestamp": "2025-12-29T10:30:45Z",
  "message": "CSV import completed",
  "data": {
    "table_name": "users",
    "total_records": 100,
    "inserted": 98,
    "failed": 2,
    "errors": [
      "Record 5: Duplicate entry for primary key",
      "Record 87: Invalid email format"
    ]
  },
  "retry_count": 0
}
```

---

#### 7. CSV EXPORT: `GET /api/batch/{tableName}/export`
Export all records from a table as downloadable CSV.

**Response**:
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename=users_export.csv`

**CSV Content**:
```
id,name,email,age
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,28
...
```

---

## Testing with curl

### Setup (Environment)
```bash
# Create a test database and table
mysql -u root -p -e "
CREATE DATABASE IF NOT EXISTS test_db;
CREATE TABLE test_db.users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  age INT
);
"

# Set environment variables
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=test_db
export DB_PORT=3306
```

---

### Test 1: Create (INSERT)
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    }
  }'
```

**Expected**: `200 OK` with `rows_affected: 1`

---

### Test 2: Retrieve All
```bash
curl -X GET http://localhost:8000/api/users/query
```

**Expected**: `200 OK` with list of all users.

---

### Test 3: Retrieve with Filter
```bash
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "age": 30
    }
  }'
```

**Expected**: `200 OK` with filtered users (age=30).

---

### Test 4: Update
```bash
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
```

**Expected**: `200 OK` with `rows_affected: 1`

---

### Test 5: Delete
```bash
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "id": 1
    }
  }'
```

**Expected**: `200 OK` with `rows_affected: 1`

---

### Test 6: CSV Import
```bash
# Create a test CSV file
cat > /tmp/users.csv << EOF
name,email,age
Alice Johnson,alice@example.com,28
Bob Smith,bob@example.com,32
Charlie Brown,charlie@example.com,25
EOF

# Upload the CSV
curl -X POST http://localhost:8000/api/batch/import \
  -F "file=@/tmp/users.csv"
```

**Expected**: `200 OK` with import statistics.

---

### Test 7: CSV Export
```bash
curl -X GET http://localhost:8000/api/users/export \
  -o users_export.csv

# View the exported CSV
cat users_export.csv
```

**Expected**: Downloaded CSV file with all users.

---

### Test 8: Error Handling - Non-existent Table
```bash
curl -X POST http://localhost:8000/api/nonexistent \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "test"}}'
```

**Expected**: `404 Not Found` with error response.

---

### Test 9: Error Handling - Missing WHERE Clause in DELETE
```bash
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

**Expected**: `400 Bad Request` with safety warning.

---

### Test 10: Timeout Simulation (Stressing Resiliency)
```bash
# Simulate slow database by adding network delay
# (Linux/Mac): Use tc (traffic control) or simulate with slow queries

# Or test with a deliberately slow query by creating a stored procedure
# that takes time to execute
```

---

## Running the Application

### Option 1: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker
```bash
# Build image
docker build -t api-server .

# Run container
docker run -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_USER=root \
  -e DB_PASSWORD=password \
  -e DB_NAME=test_db \
  api-server
```

---

## Performance & Reliability Features

1. **Exponential Backoff**: Prevents thundering herd and allows graceful degradation
2. **Parameterized Queries**: All queries use `%s` placeholders to prevent SQL injection
3. **Table Validation**: Every operation checks table existence via `INFORMATION_SCHEMA`
4. **Streaming CSV Export**: Large datasets don't cause OOM errors
5. **Comprehensive Logging**: All operations logged at INFO/DEBUG/ERROR levels
6. **Standardized Responses**: Consistent JSON schema with timestamps and error codes
7. **Connection Pooling**: Reuses database connections efficiently

---

## Error Codes Reference

| Code | Meaning | Retry Behavior |
|------|---------|----------------|
| 200 | Success | N/A |
| 400 | Bad Request | No retry |
| 404 | Not Found | No retry |
| 500 | Server Error | No retry (log only) |
| 503 | Service Unavailable | Database offline |
| 504 | Gateway Timeout | Automatic retry with backoff |

---

## Security Considerations

1. ✅ **SQL Injection**: All queries parameterized
2. ✅ **Schema Validation**: Table existence checked before execution
3. ✅ **DELETE Safety**: Requires WHERE clause to prevent accidental bulk deletes
4. ✅ **UPDATE Safety**: Requires WHERE clause to prevent accidental bulk updates
5. ⚠️ **Authentication**: Not implemented (add JWT middleware as needed)
6. ⚠️ **Rate Limiting**: Not implemented (add RateLimiter middleware as needed)

---

## Extending the API

### Add Authentication
```python
# Add to main.py
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Implement JWT validation
    pass

# Add to route: async def create_record(..., verified=Depends(verify_token))
```

### Add Rate Limiting
```bash
pip install slowapi
```

### Add Request Logging
```python
from fastapi.middleware import trustedhost
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])
```

---

## Troubleshooting

### "Database not available" (503)
- Check DB_HOST, DB_USER, DB_PASSWORD, DB_NAME environment variables
- Verify MySQL server is running
- Check network connectivity

### "Table does not exist" (404)
- Verify table exists in database: `SHOW TABLES;`
- Check table name spelling (case-sensitive on Linux)

### "Operation timed out" (504)
- Database is slow or unresponsive
- Check MySQL server logs
- Increase timeout limits in `app/core/resiliency.py`

### CSV Import Fails
- Verify CSV headers match database columns
- Check for encoding issues (UTF-8 required)
- Verify data types match column types (e.g., INT for age)

---

## Next Steps

1. **Add JWT Authentication** for API security
2. **Implement Rate Limiting** to protect against DoS
3. **Add API Documentation** via Swagger UI (auto-generated)
4. **Implement Request Validation** for stronger type checking
5. **Add Unit Tests** for all endpoints
6. **Deploy to Production** (AWS, GCP, Azure, etc.)

---

## License

This project is provided as-is for educational and commercial use.
