# 🚀 Quick Start Checklist

Follow these steps to get your production API up and running in minutes!

## Step 1: Environment Setup (2 minutes)

### 1.1 Verify Python Installation
```bash
python --version  # Should be 3.8+
pip --version
```

### 1.2 Install Dependencies
```bash
pip install -r requirements.txt
```

**What gets installed:**
- fastapi - Web framework
- uvicorn - ASGI server
- pydantic - Data validation
- python-dotenv - Environment variables
- aiomysql - Async MySQL driver
- PyMySQL - MySQL protocol support
- pytest, httpx - Testing tools

### 1.3 Configure Environment Variables
```bash
# Create .env file (or update existing)
cat > .env << EOF
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=test_db
DB_PORT=3306
EOF
```

---

## Step 2: Database Setup (5 minutes)

### 2.1 Start MySQL Server
```bash
# macOS with Homebrew
brew services start mysql

# Or manual start
mysql.server start

# Verify it's running
mysql -u root -e "SELECT 1"
```

### 2.2 Create Test Database
```bash
mysql -u root -e "
CREATE DATABASE IF NOT EXISTS test_db;

CREATE TABLE test_db.users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE,
  age INT
);

-- Insert sample data
INSERT INTO test_db.users (name, email, age) VALUES
('Alice Johnson', 'alice@example.com', 28),
('Bob Smith', 'bob@example.com', 32),
('Charlie Brown', 'charlie@example.com', 25);

-- Verify
SELECT * FROM test_db.users;
"
```

**Expected Output:**
```
id | name            | email              | age
1  | Alice Johnson   | alice@example.com  | 28
2  | Bob Smith       | bob@example.com    | 32
3  | Charlie Brown   | charlie@example.com| 25
```

---

## Step 3: Start the API Server (1 minute)

### 3.1 Option A: Direct Python
```bash
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
Creating database connection pool.
Database connection pool created.
```

### 3.2 Option B: Uvicorn with Auto-reload
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3.3 Verify API is Running
```bash
curl http://localhost:8000/
# Should return: {"message": "Hello, World"}
```

---

## Step 4: Test the API (5 minutes)

### 4.1 Test CREATE (INSERT)
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Diana Prince",
      "email": "diana@example.com",
      "age": 26
    }
  }'

# Expected: HTTP 200, rows_affected: 1
```

### 4.2 Test RETRIEVE All
```bash
curl http://localhost:8000/api/users/query

# Expected: HTTP 200, list of 4 users
```

### 4.3 Test RETRIEVE with Filter
```bash
curl -X POST http://localhost:8000/api/users/query \
  -H "Content-Type: application/json" \
  -d '{"input": {"age": 28}}'

# Expected: HTTP 200, returns Alice (age 28)
```

### 4.4 Test UPDATE
```bash
curl -X PUT http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"age": 29},
    "where": {"id": 1}
  }'

# Expected: HTTP 200, rows_affected: 1
```

### 4.5 Test DELETE
```bash
curl -X DELETE http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"input": {"id": 4}}'

# Expected: HTTP 200, rows_affected: 1 (Diana deleted)
```

### 4.6 Test CSV Import
```bash
# Create test CSV
cat > /tmp/test_import.csv << EOF
name,email,age
Eve Wilson,eve@example.com,29
Frank Miller,frank@example.com,31
EOF

# Import
curl -X POST http://localhost:8000/api/batch/import \
  -F "file=@/tmp/test_import.csv"

# Expected: HTTP 200, inserted: 2, failed: 0
```

### 4.7 Test CSV Export
```bash
curl -X GET http://localhost:8000/api/users/export \
  -o users_export.csv

cat users_export.csv
# Should show CSV with all users
```

---

## Step 5: Verify Full API Functionality (Checklist)

- [ ] API server starts without errors
- [ ] `GET /` returns "Hello, World"
- [ ] CREATE inserts new user successfully
- [ ] RETRIEVE returns all users
- [ ] RETRIEVE with filter works correctly
- [ ] UPDATE modifies user data
- [ ] DELETE removes user
- [ ] CSV import inserts multiple rows
- [ ] CSV export generates valid CSV file
- [ ] Error handling returns proper error codes

---

## Step 6: Explore the Implementation

### Read the Documentation
1. **DELIVERY_SUMMARY.md** - Overview of what you got
2. **API_DOCUMENTATION.md** - Complete API reference
3. **ARCHITECTURE.md** - System design details

### Review the Code
```bash
# Core modules
cat app/core/resiliency.py    # Retry logic
cat app/core/database.py      # Query execution
cat app/utils/error_handler.py # Error responses

# Route handlers
cat app/routes/crud.py        # CRUD endpoints
cat app/routes/csv_routes.py  # CSV endpoints

# Services
cat app/services/csv_service.py # CSV processing
```

### Check the Test Suite
```bash
# Run existing tests
python -m pytest test_main.py -v

# The tests verify:
# - Root endpoint works
# - Homepage endpoint works
# - Error handling works
```

---

## Step 7: Customize for Your Use Case

### 7.1 Add Your Own Table
```bash
# Create a new table
mysql -u root -e "
USE test_db;
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10,2),
  stock INT
);

INSERT INTO products (name, price, stock) VALUES
('Widget', 9.99, 100),
('Gadget', 19.99, 50);
"

# Now use the API with products table
curl -X POST http://localhost:8000/api/products/query

# The API automatically adapts to any table!
```

### 7.2 Add Authentication (Optional)
```python
# Install JWT library
pip install python-jose[cryptography]

# Add to main.py:
from fastapi.security import HTTPBearer
from fastapi import Depends

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Implement JWT validation
    pass

# Add to routes:
# async def create_record(..., token = Depends(verify_token))
```

### 7.3 Add Rate Limiting (Optional)
```bash
pip install slowapi

# Then configure SlowAPI middleware in main.py
```

---

## Step 8: Deploy to Production

### Option 1: Docker Deployment
```bash
# Build the image
docker build -t my-api .

# Run the container
docker run -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_USER=root \
  -e DB_PASSWORD=password \
  -e DB_NAME=test_db \
  my-api
```

### Option 2: Cloud Deployment
**AWS Elastic Beanstalk:**
```bash
eb init
eb create production-env
eb deploy
```

**Google Cloud Run:**
```bash
gcloud run deploy my-api \
  --source . \
  --platform managed \
  --region us-central1
```

**Heroku:**
```bash
heroku create my-api
git push heroku main
heroku config:set DB_HOST=your_db_host
```

---

## Troubleshooting

### Issue: "Database not available" (503)
**Solution:**
```bash
# Check MySQL is running
mysql -u root -e "SELECT 1"

# Verify .env file is set correctly
cat .env

# Check DB credentials
mysql -u root -p your_password -e "SELECT 1 FROM test_db.users"
```

### Issue: "Table does not exist" (404)
**Solution:**
```bash
# Verify table exists
mysql -u root -e "SHOW TABLES FROM test_db;"

# Create if missing
mysql -u root -e "
USE test_db;
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  age INT
);
"
```

### Issue: "Connection refused"
**Solution:**
```bash
# Start MySQL server
brew services start mysql

# Or if using Docker
docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql
```

### Issue: "Module not found"
**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify Python path
python -c "import app.core.resiliency; print('OK')"
```

---

## Next Steps After Verification

1. ✅ Review API_DOCUMENTATION.md for all endpoints
2. ✅ Study ARCHITECTURE.md for system design
3. ✅ Run all test examples from TESTING_GUIDE.sh
4. ✅ Customize the code for your use case
5. ✅ Add authentication/authorization
6. ✅ Set up monitoring and logging
7. ✅ Deploy to production

---

## Summary

You now have a **production-ready REST API** with:
- ✅ Dynamic CRUD for any table
- ✅ Automatic retry with exponential backoff
- ✅ SQL injection prevention
- ✅ CSV batch processing
- ✅ Standardized error responses
- ✅ Comprehensive logging
- ✅ Full documentation

**Time to completion: ~20 minutes**

Enjoy building! 🎉
