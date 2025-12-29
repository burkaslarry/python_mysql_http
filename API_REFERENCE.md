# 📊 Visual API Reference Guide

## API Endpoints Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI REST API Gateway                     │
│                   (http://localhost:8000)                       │
└─────────────────────────────────────────────────────────────────┘

├─ /                                          [GET]
│  └─ Returns: {"message": "Hello, World"}
│
├─ /api/homepage                              [GET]
│  └─ Returns: Homepage JSON data
│
├─ CRUD Operations (Table-Agnostic)
│  │
│  ├─ /api/{tableName}                       [POST] - CREATE
│  │  ├─ Request: {"input": {...data}}
│  │  └─ Response: {"timestamp":"...", "data": {"rows_affected": 1}}
│  │
│  ├─ /api/{tableName}/query                 [GET] - RETRIEVE ALL
│  │  ├─ Request: None (no body)
│  │  └─ Response: {"timestamp":"...", "data": [...records...]}
│  │
│  ├─ /api/{tableName}/query                 [POST] - RETRIEVE FILTERED
│  │  ├─ Request: {"input": {"column": "value", ...}}
│  │  └─ Response: {"timestamp":"...", "data": [...filtered...]}
│  │
│  ├─ /api/{tableName}                       [PUT] - UPDATE
│  │  ├─ Request: {"input": {...new_values...}, "where": {...conditions...}}
│  │  └─ Response: {"timestamp":"...", "data": {"rows_affected": N}}
│  │
│  └─ /api/{tableName}                       [DELETE] - DELETE
│     ├─ Request: {"input": {...where_conditions...}}
│     └─ Response: {"timestamp":"...", "data": {"rows_affected": N}}
│
└─ CSV Operations
   │
   ├─ /api/batch/import                      [POST] - IMPORT CSV
   │  ├─ Request: multipart/form-data (file=@data.csv)
   │  └─ Response: {"timestamp":"...", "data": {
   │                  "table_name": "data",
   │                  "total_records": 100,
   │                  "inserted": 98,
   │                  "failed": 2,
   │                  "errors": [...]
   │                }}
   │
   └─ /api/batch/{tableName}/export          [GET] - EXPORT CSV
      ├─ Request: None
      └─ Response: CSV file download
         (Content-Type: text/csv)
```

---

## Request/Response Examples Matrix

### 1. CREATE (POST /api/users)

```
REQUEST:
┌────────────────────────────────────────┐
│ POST /api/users                        │
│ Content-Type: application/json         │
│                                        │
│ {                                      │
│   "input": {                           │
│     "name": "John Doe",                │
│     "email": "john@example.com",       │
│     "age": 30                          │
│   }                                    │
│ }                                      │
└────────────────────────────────────────┘
        │
        ▼ Process: Validate → Insert → Return
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "Record inserted successfully",     │
│   "data": {                            │
│     "rows_affected": 1                 │
│   },                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 2. RETRIEVE (GET /api/users/query)

```
REQUEST:
┌────────────────────────────────────────┐
│ GET /api/users/query                   │
│ Content-Type: application/json         │
│                                        │
│ (No body)                              │
└────────────────────────────────────────┘
        │
        ▼ Process: Validate → Select All → Return
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "Retrieved 3 record(s)",            │
│   "data": [                            │
│     {                                  │
│       "id": 1,                         │
│       "name": "John Doe",              │
│       "email": "john@example.com",     │
│       "age": 30                        │
│     },                                 │
│     {                                  │
│       "id": 2,                         │
│       "name": "Jane Smith",            │
│       "email": "jane@example.com",     │
│       "age": 28                        │
│     },                                 │
│     ...                                │
│   ],                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 3. RETRIEVE with FILTER (POST /api/users/query)

```
REQUEST:
┌────────────────────────────────────────┐
│ POST /api/users/query                  │
│ Content-Type: application/json         │
│                                        │
│ {                                      │
│   "input": {                           │
│     "age": 30                          │
│   }                                    │
│ }                                      │
└────────────────────────────────────────┘
        │
        ▼ Process: Validate → Select WHERE → Return
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "Retrieved 1 record(s)",            │
│   "data": [                            │
│     {                                  │
│       "id": 1,                         │
│       "name": "John Doe",              │
│       "email": "john@example.com",     │
│       "age": 30                        │
│     }                                  │
│   ],                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 4. UPDATE (PUT /api/users)

```
REQUEST:
┌────────────────────────────────────────┐
│ PUT /api/users                         │
│ Content-Type: application/json         │
│                                        │
│ {                                      │
│   "input": {                           │
│     "age": 31,                         │
│     "email": "new@example.com"         │
│   },                                   │
│   "where": {                           │
│     "id": 1                            │
│   }                                    │
│ }                                      │
└────────────────────────────────────────┘
        │
        ▼ Process: Validate → Update WHERE → Return
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "Record updated successfully",      │
│   "data": {                            │
│     "rows_affected": 1                 │
│   },                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 5. DELETE (DELETE /api/users)

```
REQUEST:
┌────────────────────────────────────────┐
│ DELETE /api/users                      │
│ Content-Type: application/json         │
│                                        │
│ {                                      │
│   "input": {                           │
│     "id": 2                            │
│   }                                    │
│ }                                      │
└────────────────────────────────────────┘
        │
        ▼ Process: Validate → Delete WHERE → Return
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "Record deleted successfully",      │
│   "data": {                            │
│     "rows_affected": 1                 │
│   },                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 6. CSV IMPORT (POST /api/batch/import)

```
REQUEST:
┌────────────────────────────────────────┐
│ POST /api/batch/import                 │
│ Content-Type: multipart/form-data      │
│                                        │
│ file: @users.csv                       │
│ (File content: CSV with headers)       │
└────────────────────────────────────────┘
        │
        ▼ Process: Parse → Insert Rows → Track Errors
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ {                                      │
│   "timestamp":                         │
│    "2025-12-29T10:30:45.123456Z",     │
│   "message":                           │
│    "CSV import completed",             │
│   "data": {                            │
│     "table_name": "users",             │
│     "total_records": 100,              │
│     "inserted": 98,                    │
│     "failed": 2,                       │
│     "errors": [                        │
│       "Record 5: Duplicate key",       │
│       "Record 87: Invalid email"       │
│     ]                                  │
│   },                                   │
│   "retry_count": 0                     │
│ }                                      │
└────────────────────────────────────────┘
```

---

### 7. CSV EXPORT (GET /api/batch/{tableName}/export)

```
REQUEST:
┌────────────────────────────────────────┐
│ GET /api/batch/users/export            │
│ Accept: text/csv                       │
│                                        │
│ (No body)                              │
└────────────────────────────────────────┘
        │
        ▼ Process: Select All → Stream CSV
        │
RESPONSE (200 OK):
┌────────────────────────────────────────┐
│ Content-Type: text/csv                 │
│ Content-Disposition: attachment        │
│                                        │
│ id,name,email,age                      │
│ 1,John Doe,john@example.com,30         │
│ 2,Jane Smith,jane@example.com,28       │
│ 3,Bob Johnson,bob@example.com,35       │
│ ...                                    │
└────────────────────────────────────────┘
```

---

## Error Response Examples

### Error 404: Table Not Found

```json
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "404",
  "message": "Table 'nonexistent_table' does not exist",
  "retry_count": 0,
  "details": null
}
```

### Error 400: Bad Request (Missing WHERE)

```json
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "400",
  "message": "Invalid operation: DELETE requires WHERE conditions for safety",
  "retry_count": 0,
  "details": null
}
```

### Error 503: Service Unavailable (DB Offline)

```json
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "503",
  "message": "Database not available",
  "retry_count": 0,
  "details": null
}
```

### Error 504: Gateway Timeout (All Retries Failed)

```json
{
  "timestamp": "2025-12-29T10:30:45.123456Z",
  "error_code": "504",
  "message": "Database operation timed out after 4 attempts. Last error: connection timeout",
  "retry_count": 4,
  "details": null
}
```

---

## HTTP Status Codes Summary

| Code | Meaning | When | Retry? |
|------|---------|------|--------|
| **200** | OK | Successful operation | No |
| **400** | Bad Request | Validation error, missing WHERE | No |
| **404** | Not Found | Table doesn't exist | No |
| **500** | Server Error | Unexpected error | No |
| **503** | Service Unavailable | Database offline | Auto-retry |
| **504** | Gateway Timeout | All retries exhausted | No |

---

## Retry Flow Visualization

```
User Request
  │
  ▼
Attempt 1: 200ms timeout
  ├─ Success? ────────────────────► HTTP 200 ✓
  └─ Timeout/Error
     │
     ├─ All retries done? ──► HTTP 504 ✗
     │
     └─ More retries? ──► Sleep 400ms
        │
        ▼
Attempt 2: 400ms timeout
  ├─ Success? ────────────────────► HTTP 200 ✓
  └─ Timeout/Error
     │
     ├─ All retries done? ──► HTTP 504 ✗
     │
     └─ More retries? ──► Sleep 800ms
        │
        ▼
Attempt 3: 800ms timeout
  ├─ Success? ────────────────────► HTTP 200 ✓
  └─ Timeout/Error
     │
     ├─ All retries done? ──► HTTP 504 ✗
     │
     └─ More retries? ──► Sleep 1600ms
        │
        ▼
Attempt 4: 1600ms timeout
  ├─ Success? ────────────────────► HTTP 200 ✓
  └─ Timeout/Error
     │
     └─► HTTP 504 (All retries exhausted) ✗
```

---

## Request Format Cheat Sheet

### CREATE Format
```json
{
  "input": {
    "column1": "value1",
    "column2": "value2"
  }
}
```

### RETRIEVE Format (No Filter)
```
GET /api/{tableName}/query
```

### RETRIEVE Format (With Filter)
```json
{
  "input": {
    "column1": "value1",
    "column2": "value2"
  }
}
```

### UPDATE Format
```json
{
  "input": {
    "column1": "new_value1",
    "column2": "new_value2"
  },
  "where": {
    "id": 1
  }
}
```

### DELETE Format
```json
{
  "input": {
    "id": 1
  }
}
```

### CSV Format (for import)
```
name,email,age
John Doe,john@example.com,30
Jane Smith,jane@example.com,28
```

---

## Quick Copy-Paste Commands

### Create
```bash
curl -X POST http://localhost:8000/api/TABLENAME \
  -H "Content-Type: application/json" \
  -d '{"input": {"COL1": "VAL1", "COL2": "VAL2"}}'
```

### Read All
```bash
curl http://localhost:8000/api/TABLENAME/query
```

### Read Filtered
```bash
curl -X POST http://localhost:8000/api/TABLENAME/query \
  -H "Content-Type: application/json" \
  -d '{"input": {"COLUMN": "VALUE"}}'
```

### Update
```bash
curl -X PUT http://localhost:8000/api/TABLENAME \
  -H "Content-Type: application/json" \
  -d '{"input": {"COL": "VAL"}, "where": {"id": 1}}'
```

### Delete
```bash
curl -X DELETE http://localhost:8000/api/TABLENAME \
  -H "Content-Type: application/json" \
  -d '{"input": {"id": 1}}'
```

### Import CSV
```bash
curl -X POST http://localhost:8000/api/batch/import \
  -F "file=@FILENAME.csv"
```

### Export CSV
```bash
curl -X GET http://localhost:8000/api/TABLENAME/export \
  -o TABLENAME.csv
```

---

## Response Time Expectations

| Operation | Timeout | Typical Response |
|-----------|---------|-----------------|
| CREATE | 200ms | 50-100ms |
| RETRIEVE (1-10 rows) | 200ms | 30-50ms |
| RETRIEVE (1000 rows) | 400ms | 100-200ms |
| UPDATE (1 record) | 200ms | 40-80ms |
| DELETE (1 record) | 200ms | 40-80ms |
| CSV IMPORT (100 rows) | 2000ms | 500-1000ms |
| CSV EXPORT (1000 rows) | 400ms | 100-200ms |

---

## Performance Tips

1. **Use Filters** - Don't always retrieve all records
   ```json
   {"input": {"age": 30}}  // Better
   ```

2. **Batch Operations** - Use CSV import for bulk inserts
   ```bash
   # Good: 1000 rows in 1 request
   curl -X POST http://localhost:8000/api/batch/import -F "file=@data.csv"
   
   # Bad: 1000 individual POST requests
   for i in {1..1000}; do curl -X POST ...; done
   ```

3. **Specify WHERE Conditions** - Reduce database load
   ```json
   {"where": {"status": "active", "age": 25}}  // Good
   {"where": {"id": 1}}  // Better - uses primary key
   ```

---

## Common Patterns

### Pattern 1: Check if Record Exists
```bash
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{"input": {"email": "john@example.com"}}'

# Returns empty array if not found
```

### Pattern 2: Get Total Count
```bash
curl http://localhost:8000/api/users/query \
  | jq 'length'  # Count records
```

### Pattern 3: Update All Records of a Type
```bash
curl -X PUT http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"input": {"status": "archived"}, "where": {"age": 100}}'
```

### Pattern 4: Bulk Delete
```bash
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"input": {"status": "inactive"}}'
```

---

This quick reference should help you get started immediately!
