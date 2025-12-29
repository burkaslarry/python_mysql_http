# System Architecture Overview

## High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                      │
│                       (main.py - Entry Point)                   │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├─────────────────────────────────────────┐
               │                                         │
               ▼                                         ▼
        ┌──────────────┐                          ┌──────────────┐
        │   CRUD       │                          │     CSV      │
        │   Routes     │                          │    Routes    │
        │ (crud.py)    │                          │(csv_routes)  │
        └──────┬───────┘                          └──────┬───────┘
               │                                         │
               └──────────────┬──────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        ┌──────────────┐            ┌──────────────┐
        │ Resiliency   │            │     CSV      │
        │  Wrapper     │            │    Service   │
        │(resiliency)  │            │(csv_service) │
        └──────┬───────┘            └──────┬───────┘
               │                           │
               └──────────────┬────────────┘
                              │
                ┌─────────────┴────────────┐
                │                          │
                ▼                          ▼
        ┌──────────────┐          ┌───────────────┐
        │   Database   │          │    Error      │
        │    Core      │          │   Handler     │
        │(database.py) │          │(error_handler)│
        └──────┬───────┘          └───────────────┘
               │
               ▼
        ┌──────────────────────┐
        │  MySQL Database      │
        │  (via aiomysql pool) │
        └──────────────────────┘
```

## Request Flow

### Example: CREATE Request

```
Client
  │
  ├─ POST /api/users
  │  Body: { "input": { "name": "John", "email": "john@example.com" } }
  │
  ▼
┌─────────────────────────────────┐
│    FastAPI Routing Layer        │
│  (app.include_router)           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   CRUD Route Handler            │
│  (routes/crud.py:create_record) │
│  - Validates request format     │
│  - Parses "input" field         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Resiliency Wrapper             │
│ (core/resiliency.py)            │
│ - Wraps database call           │
│ - Implements timeout logic      │
│ - Manages retry schedule        │
└────────────┬────────────────────┘
             │
      ┌──────┴───────┬──────────┬──────────┐
      │              │          │          │
      ▼              ▼          ▼          ▼
   Attempt 0     Attempt 1  Attempt 2  Attempt 3
   (200ms)       (400ms)    (800ms)    (1600ms)
                 (wait 400ms)(wait 800ms)(wait 1600ms)
      │              │          │          │
      └──────┬───────┴──────────┴──────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Database Core                 │
│ (core/database.py)              │
│ - Validate table existence      │
│ - Build parameterized query     │
│ - Execute INSERT command        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   MySQL Connection Pool         │
│ (aiomysql)                      │
│ - Get connection from pool      │
│ - Execute query                 │
│ - Release connection            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Database Engine               │
│ (MySQL Server)                  │
│ - Process INSERT                │
│ - Return affected rows          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Error Handler                 │
│ (utils/error_handler.py)        │
│ - Package response              │
│ - Add timestamp                 │
│ - Add retry_count               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   FastAPI Response              │
│ HTTP 200 OK                     │
│ {                               │
│   "timestamp": "...",           │
│   "message": "...",             │
│   "data": { ... },              │
│   "retry_count": 0              │
│ }                               │
└────────────┬────────────────────┘
             │
             ▼
           Client
```

## Module Responsibilities

### 1. **app/core/resiliency.py**
- **Responsibility**: Retry logic with exponential backoff
- **Key Functions**:
  - `execute_with_retries()` - Wraps async functions with retry logic
  - `execute_with_fallback()` - Returns fallback value on failure
- **Exceptions**:
  - `GatewayTimeoutException` (504) - All retries exhausted
  - `ServiceUnavailableException` (503) - Database unavailable

### 2. **app/core/database.py**
- **Responsibility**: Database operations with validation
- **Key Functions**:
  - `table_exists()` - Validates table via INFORMATION_SCHEMA
  - `execute_insert()` - Parameterized INSERT
  - `execute_select()` - Parameterized SELECT with WHERE
  - `execute_update()` - Parameterized UPDATE with safety checks
  - `execute_delete()` - Parameterized DELETE with safety checks
- **Security**: All queries use parameterized statements (`%s` placeholders)

### 3. **app/routes/crud.py**
- **Responsibility**: HTTP endpoint handlers for CRUD operations
- **Endpoints**:
  - `POST /api/{table_name}` - CREATE
  - `GET /api/{table_name}/query` - RETRIEVE all
  - `POST /api/{table_name}/query` - RETRIEVE with filter
  - `PUT /api/{table_name}` - UPDATE
  - `DELETE /api/{table_name}` - DELETE
- **Features**:
  - Integrates resiliency wrapper
  - Validates table existence
  - Standardized error responses

### 4. **app/services/csv_service.py**
- **Responsibility**: CSV parsing and database operations
- **Key Functions**:
  - `parse_csv_file()` - Extract filename as table name, parse rows
  - `batch_import_csv()` - Iterate records, track successes/failures
  - `export_to_csv()` - Stream data to prevent memory overflow
- **Features**:
  - Per-record error tracking
  - Streaming export for large datasets

### 5. **app/routes/csv_routes.py**
- **Responsibility**: HTTP handlers for CSV operations
- **Endpoints**:
  - `POST /api/batch/import` - Upload and import CSV
  - `GET /api/batch/{table_name}/export` - Download CSV
- **Features**:
  - File validation
  - Streaming response

### 6. **app/utils/error_handler.py**
- **Responsibility**: Standardized error/success responses
- **Classes**:
  - `ErrorResponse` - Pydantic model for errors
  - `SuccessResponse` - Pydantic model for success
- **Functions**:
  - `create_error_response()` - Build error JSON
  - `create_success_response()` - Build success JSON
  - `log_error()` - Log with context

### 7. **app/schemas/requests.py**
- **Responsibility**: Request validation schemas
- **Classes**:
  - `CRUDRequest` - { "input": { ...data } }
  - `UpdateRequest` - { "input": { ...new_values }, "where": { ...conditions } }
  - `DeleteRequest` - { "input": { ...WHERE_conditions } }

## Data Flow: Retry Mechanism

```
Database Call
  │
  ▼ [Execute async function with timeout]
  │
  ├─ Success? ──────────────────────► Return Result
  │
  ├─ Timeout/Error ─────┐
  │                      │
  │   Retry Attempt 1?   │
  │   (200ms elapsed)    │
  │      No ◄────────────┴─────────► Return GatewayTimeoutException
  │      │
  │      Yes
  │      │
  │      ├─ Wait 400ms
  │      │
  │      ├─ Execute with 400ms timeout
  │      │
  │      ├─ Success? ──────────────► Return Result
  │      │
  │      ├─ Timeout/Error ──┐
  │      │                  │
  │      │  Retry Attempt 2?│
  │      │     No ◄─────────┴────────► Return GatewayTimeoutException
  │      │     │
  │      │     Yes
  │      │     │
  │      │     ├─ Wait 800ms
  │      │     │
  │      │     ├─ Execute with 800ms timeout
  │      │     │
  │      │     ├─ Success? ───────► Return Result
  │      │     │
  │      │     ├─ Timeout/Error ─┐
  │      │     │                 │
  │      │     │ Retry Attempt 3?│
  │      │     │    No ◄─────────┴─────► Return GatewayTimeoutException
  │      │     │    │
  │      │     │    Yes
  │      │     │    │
  │      │     │    ├─ Wait 1600ms
  │      │     │    │
  │      │     │    ├─ Execute with 1600ms timeout
  │      │     │    │
  │      │     │    ├─ Success? ──► Return Result
  │      │     │    │
  │      │     │    └─ Failure ────► Return GatewayTimeoutException
  │      │     │
  │      └─────┘
  │
  └──────────────────────────────────► All Attempts Exhausted
```

## Concurrency Model

The system uses **async/await** for high-performance concurrent request handling:

```
Request 1: POST /api/users
├─ Async handler starts
├─ Resiliency wrapper (non-blocking)
├─ Database query (awaitable)
└─ Response sent

Request 2: GET /api/products/query
├─ Async handler starts (concurrent!)
├─ Resiliency wrapper (non-blocking)
├─ Database query (awaitable)
└─ Response sent

Request 3: PUT /api/orders
├─ Async handler starts (concurrent!)
├─ ... (same pattern)
```

Benefits:
- ✅ Single-threaded, highly efficient
- ✅ Handles 1000s of concurrent requests
- ✅ Non-blocking I/O (doesn't wait for DB sequentially)
- ✅ Lower resource overhead than multi-threading

## Error Handling Strategy

```
Database Operation
  │
  ├─ Normal Error (e.g., duplicate key)
  │  └─ DatabaseError
  │     └─ HTTP 400 Bad Request
  │
  ├─ Timeout (connection/query timeout)
  │  └─ asyncio.TimeoutError
  │     └─ Retry wrapper catches
  │        └─ If retries exhausted: HTTP 504 Gateway Timeout
  │        └─ If retries pending: Sleep and retry
  │
  ├─ Database Unavailable
  │  └─ ServiceUnavailableException
  │     └─ HTTP 503 Service Unavailable
  │
  ├─ Table Not Found
  │  └─ TableNotFoundError
  │     └─ HTTP 404 Not Found
  │
  └─ Unexpected Error
     └─ Generic Exception
        └─ HTTP 500 Internal Server Error
```

## Security Architecture

```
Incoming Request
  │
  ├─ CORS Middleware Check
  │  └─ Allowed origins: * (configurable)
  │
  ├─ Route Handler
  │  │
  │  ├─ Input Validation
  │  │  ├─ Pydantic schema validation
  │  │  └─ Type checking
  │  │
  │  └─ Table Existence Check
  │     └─ INFORMATION_SCHEMA query
  │
  ├─ Database Core
  │  │
  │  ├─ Parameterized Query Building
  │  │  ├─ Column names escaped with backticks
  │  │  └─ Values always use %s placeholders
  │  │
  │  ├─ Safety Guards
  │  │  ├─ DELETE requires WHERE clause
  │  │  └─ UPDATE requires WHERE clause
  │  │
  │  └─ Execution with Connection Pool
  │     └─ Connection isolation, auto-commit
  │
  └─ Response (Sanitized)
     └─ No sensitive info in errors
```

## Scalability Considerations

### Current Architecture Limits:
- **Database Connections**: Limited by MySQL `max_connections` setting
- **Memory**: Streaming CSV prevents OOM on large exports
- **CPU**: Async I/O means low CPU usage even under high load
- **Network**: Typical HTTP bandwidth limits apply

### Scaling Options:
1. **Horizontal**: Deploy multiple instances behind load balancer
2. **Database Replication**: Master-slave for read scaling
3. **Caching**: Add Redis for frequently accessed tables
4. **Rate Limiting**: Add SlowAPI for API protection
5. **Async Workers**: Use Gunicorn with multiple uvicorn workers

Example Deployment:
```
Load Balancer (nginx)
  ├─ API Instance 1
  ├─ API Instance 2
  ├─ API Instance 3
  └─ API Instance N
       │
       └─ MySQL Database (Primary)
           └─ MySQL Read Replicas (Secondary)
```

## Future Enhancements

1. **Authentication & Authorization**
   - JWT token validation
   - Role-based access control (RBAC)

2. **Advanced Querying**
   - Support for OR conditions
   - Range queries (>, <, >=, <=)
   - LIKE pattern matching
   - JOIN operations

3. **Caching Layer**
   - Redis integration
   - Cache invalidation strategies

4. **Monitoring & Observability**
   - Prometheus metrics
   - OpenTelemetry tracing
   - Structured logging (JSON)

5. **API Documentation**
   - Swagger UI (auto-generated)
   - OpenAPI schema
   - Interactive API explorer

6. **Testing**
   - Unit tests for core modules
   - Integration tests for endpoints
   - Load testing with locust
   - Contract testing

---

## Summary

This architecture provides:
✅ **Modularity**: Clear separation of concerns
✅ **Resilience**: Automatic retry with exponential backoff
✅ **Safety**: SQL injection prevention, schema validation
✅ **Performance**: Async I/O, connection pooling, streaming
✅ **Maintainability**: Clean code, comprehensive logging
✅ **Scalability**: Ready for horizontal expansion
