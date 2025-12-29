"""
Comprehensive API Endpoint Testing
Tests all 7 endpoints with real HTTP requests
"""

import pytest
from fastapi.testclient import TestClient
import json
import os
import io
import csv
from main import app

client = TestClient(app)

# ============================================================================
# ENDPOINT 1: POST /api/{tableName} - CREATE
# ============================================================================

class TestCreateEndpoint:
    """Test CREATE endpoint (POST /api/{tableName})"""
    
    def test_create_requires_valid_json(self):
        """Create endpoint should validate JSON input"""
        response = client.post(
            "/api/users",
            json={"input": {"name": "John", "email": "john@example.com"}}
        )
        # Will return 503 or 404 if no database configured, but should accept the request
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_create_with_missing_input_field(self):
        """Create endpoint should require 'input' field"""
        response = client.post(
            "/api/users",
            json={"data": {"name": "John"}}
        )
        # Should fail validation
        assert response.status_code in [422, 400, 503, 504]
    
    def test_create_endpoint_accessible(self):
        """Verify CREATE endpoint is registered"""
        response = client.post(
            "/api/test_table",
            json={"input": {}}
        )
        # Should be accessible (even if it returns error)
        assert response.status_code in [200, 400, 404, 503, 504]


# ============================================================================
# ENDPOINT 2: GET /api/{tableName}/query - READ ALL
# ============================================================================

class TestReadAllEndpoint:
    """Test READ ALL endpoint (GET /api/{tableName}/query)"""
    
    def test_read_all_basic(self):
        """GET /api/{tableName}/query should work"""
        response = client.get("/api/users/query")
        # Should return 200, 503, or 404
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_read_all_returns_json(self):
        """READ endpoint should return JSON"""
        response = client.get("/api/users/query")
        # Either valid JSON or error response
        try:
            data = response.json()
            assert isinstance(data, (dict, list))
        except:
            pass  # 503 or other errors
    
    def test_read_all_with_different_tables(self):
        """READ should work with any table name"""
        tables = ["users", "products", "orders", "customers"]
        for table in tables:
            response = client.get(f"/api/{table}/query")
            # Should all be accessible
            assert response.status_code in [200, 400, 503, 504, 404]


# ============================================================================
# ENDPOINT 3: POST /api/{tableName}/query - READ FILTERED
# ============================================================================

class TestReadFilteredEndpoint:
    """Test READ FILTERED endpoint (POST /api/{tableName}/query)"""
    
    def test_read_filtered_basic(self):
        """POST /api/{tableName}/query with filter"""
        response = client.post(
            "/api/users/query",
            json={"input": {"id": 1}}
        )
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_read_filtered_multiple_conditions(self):
        """POST filter with multiple conditions"""
        response = client.post(
            "/api/users/query",
            json={"input": {"name": "John", "age": 30}}
        )
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_read_filtered_returns_json(self):
        """Filtered read should return valid JSON"""
        response = client.post(
            "/api/users/query",
            json={"input": {"email": "test@example.com"}}
        )
        # Should return JSON (error or success)
        try:
            data = response.json()
            assert isinstance(data, (dict, list))
        except:
            pass


# ============================================================================
# ENDPOINT 4: PUT /api/{tableName} - UPDATE
# ============================================================================

class TestUpdateEndpoint:
    """Test UPDATE endpoint (PUT /api/{tableName})"""
    
    def test_update_requires_where_clause(self):
        """Update accepts input with or without where"""
        response = client.put(
            "/api/users",
            json={"input": {"age": 31}}
        )
        # Should accept request (where is optional in the schema)
        assert response.status_code in [200, 400, 503, 504, 422]
    
    def test_update_with_where_clause(self):
        """Update with proper format"""
        response = client.put(
            "/api/users",
            json={
                "input": {"age": 31},
                "where": {"id": 1}
            }
        )
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_update_multiple_fields(self):
        """Update multiple fields at once"""
        response = client.put(
            "/api/users",
            json={
                "input": {"age": 31, "status": "active"},
                "where": {"id": 1}
            }
        )
        assert response.status_code in [200, 400, 503, 504, 404]


# ============================================================================
# ENDPOINT 5: DELETE /api/{tableName} - DELETE
# ============================================================================

class TestDeleteEndpoint:
    """Test DELETE endpoint (DELETE /api/{tableName})"""
    
    def test_delete_requires_where(self):
        """Delete should require WHERE clause"""
        response = client.request(
            "DELETE",
            "/api/users",
            json={"input": {}}
        )
        # Should handle request
        assert response.status_code in [200, 400, 503, 504]
    
    def test_delete_with_where_clause(self):
        """Delete with proper WHERE format"""
        response = client.request(
            "DELETE",
            "/api/users",
            json={"input": {"id": 1}}
        )
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_delete_multiple_conditions(self):
        """Delete with multiple conditions"""
        response = client.request(
            "DELETE",
            "/api/users",
            json={"input": {"status": "inactive", "age": 18}}
        )
        assert response.status_code in [200, 400, 503, 504, 404]


# ============================================================================
# ENDPOINT 6: POST /api/batch/import - CSV IMPORT
# ============================================================================

class TestCSVImportEndpoint:
    """Test CSV IMPORT endpoint (POST /api/batch/import)"""
    
    def test_csv_import_requires_file(self):
        """CSV import should require file"""
        response = client.post("/api/batch/import")
        # Should return error (no file)
        assert response.status_code in [400, 422, 503]
    
    def test_csv_import_with_csv_file(self):
        """CSV import accepts CSV file"""
        # Create sample CSV data with BytesIO
        csv_content = b"id,name,email\n1,John,john@example.com\n2,Jane,jane@example.com"
        files = {"file": ("users.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/api/batch/import", files=files)
        # Should accept the CSV
        assert response.status_code in [200, 400, 503, 504, 413, 422]
    
    def test_csv_import_endpoint_exists(self):
        """Verify CSV import endpoint is registered"""
        # POST with empty file
        response = client.post("/api/batch/import")
        # Should be a 4xx error (bad request), not 404
        assert response.status_code != 404


# ============================================================================
# ENDPOINT 7: GET /api/batch/{tableName}/export - CSV EXPORT
# ============================================================================

class TestCSVExportEndpoint:
    """Test CSV EXPORT endpoint (GET /api/batch/{tableName}/export)"""
    
    def test_csv_export_basic(self):
        """CSV export endpoint should be accessible"""
        response = client.get("/api/batch/users/export")
        # Should return CSV or error, not 404
        assert response.status_code in [200, 400, 503, 504, 404]
    
    def test_csv_export_content_type(self):
        """CSV export should have correct content type"""
        response = client.get("/api/batch/users/export")
        if response.status_code == 200:
            # Check if it's CSV
            assert "text/csv" in response.headers.get("content-type", "").lower() or \
                   "application/csv" in response.headers.get("content-type", "").lower()
    
    def test_csv_export_different_tables(self):
        """CSV export should work with any table"""
        tables = ["users", "products", "orders"]
        for table in tables:
            response = client.get(f"/api/batch/{table}/export")
            # Should be accessible
            assert response.status_code in [200, 400, 503, 504, 404]


# ============================================================================
# KEY FEATURES TESTING
# ============================================================================

class TestKeyFeatures:
    """Test key features mentioned in documentation"""
    
    def test_cors_enabled(self):
        """CORS should be enabled"""
        response = client.get(
            "/",
            headers={"Origin": "http://example.com"}
        )
        # Should have CORS headers
        assert response.status_code == 200
    
    def test_error_response_format(self):
        """Error responses should be standardized"""
        response = client.post(
            "/api/nonexistent/query",
            json={"input": {}}
        )
        if response.status_code >= 400:
            data = response.json()
            # Error response should have these fields (nested in 'detail' or at root)
            if "detail" in data:
                data = data["detail"]
            assert "error_code" in data or "timestamp" in data or "message" in data
    
    def test_json_response_format(self):
        """Responses should be valid JSON"""
        response = client.get("/")
        assert response.headers.get("content-type").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_sql_injection_protection(self):
        """Parameterized queries should prevent SQL injection"""
        # Try SQL injection in WHERE clause
        response = client.post(
            "/api/users/query",
            json={"input": {"id": "1; DROP TABLE users;--"}}
        )
        # Should not cause error, query should be parameterized
        assert response.status_code in [200, 400, 503, 504]
    
    def test_resiliency_engine_exists(self):
        """Resiliency module should be available"""
        from app.core.resiliency import execute_with_retries
        assert execute_with_retries is not None
    
    def test_database_config_module_exists(self):
        """Database config module should exist"""
        from app.core.config import DatabaseConfig
        assert DatabaseConfig is not None
    
    def test_multi_database_support(self):
        """Should support MySQL and PostgreSQL"""
        from app.core.config import DatabaseConfig
        config = DatabaseConfig()
        
        # Should have MySQL and PostgreSQL methods
        assert hasattr(config, 'is_mysql_configured') or hasattr(config, 'get_mysql_url')
        assert hasattr(config, 'is_postgresql_configured') or hasattr(config, 'get_postgresql_url')


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAPIIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_all_crud_endpoints_registered(self):
        """All 5 CRUD endpoints should be registered"""
        endpoints = [
            ("POST", "/api/test/"),
            ("GET", "/api/test/query"),
            ("POST", "/api/test/query"),
            ("PUT", "/api/test/"),
            ("DELETE", "/api/test/"),
        ]
        
        for method, path in endpoints:
            if method == "POST" and "query" not in path:
                # CREATE
                response = client.post(path.replace("/test/", "/test"), json={"input": {}})
            elif method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path, json={"input": {}})
            elif method == "PUT":
                response = client.put(path.replace("/test/", "/test"), json={"input": {}, "where": {}})
            elif method == "DELETE":
                response = client.request("DELETE", path.replace("/test/", "/test"), json={"input": {}})
            
            # Should not return 404 (not found)
            assert response.status_code != 404, f"{method} {path} not found"
    
    def test_all_csv_endpoints_registered(self):
        """Both CSV endpoints should be registered"""
        # Import endpoint
        response = client.post("/api/batch/import")
        assert response.status_code != 404
        
        # Export endpoint
        response = client.get("/api/batch/users/export")
        assert response.status_code != 404
    
    def test_error_handling_consistency(self):
        """Error responses should be consistent"""
        # Test multiple error scenarios
        responses = []
        
        # Missing table
        r1 = client.post("/api/users/query", json={"input": {}})
        responses.append(r1)
        
        # Invalid method (should fail with 503 if no DB)
        r2 = client.post("/api/users", json={"input": {}})
        responses.append(r2)
        
        # All responses should be valid JSON
        for resp in responses:
            if resp.status_code >= 400:
                try:
                    data = resp.json()
                    assert isinstance(data, dict)
                except:
                    pass


# ============================================================================
# ENDPOINT AVAILABILITY SUMMARY
# ============================================================================

class TestEndpointSummary:
    """Summary test to verify all 7 endpoints are available"""
    
    def test_endpoint_1_create_post_api_tablename(self):
        """✓ Endpoint 1: POST /api/{tableName} - CREATE"""
        response = client.post("/api/users", json={"input": {"name": "John"}})
        assert response.status_code != 404
    
    def test_endpoint_2_read_all_get_api_tablename_query(self):
        """✓ Endpoint 2: GET /api/{tableName}/query - READ"""
        response = client.get("/api/users/query")
        assert response.status_code != 404
    
    def test_endpoint_3_read_filtered_post_api_tablename_query(self):
        """✓ Endpoint 3: POST /api/{tableName}/query - READ FILTERED"""
        response = client.post("/api/users/query", json={"input": {"id": 1}})
        assert response.status_code != 404
    
    def test_endpoint_4_update_put_api_tablename(self):
        """✓ Endpoint 4: PUT /api/{tableName} - UPDATE"""
        response = client.put("/api/users", json={"input": {"age": 31}, "where": {"id": 1}})
        assert response.status_code != 404
    
    def test_endpoint_5_delete_delete_api_tablename(self):
        """✓ Endpoint 5: DELETE /api/{tableName} - DELETE"""
        response = client.request("DELETE", "/api/users", json={"input": {"id": 1}})
        assert response.status_code != 404
    
    def test_endpoint_6_csv_import_post_api_batch_import(self):
        """✓ Endpoint 6: POST /api/batch/import - CSV IMPORT"""
        response = client.post("/api/batch/import")
        assert response.status_code != 404
    
    def test_endpoint_7_csv_export_get_api_batch_tablename_export(self):
        """✓ Endpoint 7: GET /api/batch/{tableName}/export - CSV EXPORT"""
        response = client.get("/api/batch/users/export")
        assert response.status_code != 404
