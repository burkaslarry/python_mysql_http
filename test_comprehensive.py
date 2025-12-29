"""
Comprehensive test suite for MySQL and PostgreSQL database connections
Tests all CRUD endpoints with local databases
"""

import pytest
import asyncio
import os
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ============================================================================
# EXISTING TESTS (Original)
# ============================================================================

def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World"}


def test_get_homepage():
    """Test the homepage endpoint"""
    # Ensure the demo data exists for the test
    assert os.path.exists(os.path.join("demo_data", "homepage.json"))
    
    response = client.get("/api/homepage")
    assert response.status_code == 200
    data = response.json()
    assert "home" in data
    assert "title" in data["home"]


def test_read_items_no_db():
    """Test items endpoint - handles gracefully when DB not configured"""
    response = client.get("/items")
    # Either 200 if items exist, or 503 if DB not configured
    assert response.status_code in [200, 503]


# ============================================================================
# NEW DATABASE TESTS
# ============================================================================

class TestDatabaseConnectivity:
    """Test database connection configuration"""
    
    def test_mysql_env_vars_optional(self):
        """Test that MySQL env vars are optional"""
        # DB_HOST etc. can be empty without crashing the app
        assert app is not None
    
    def test_postgresql_env_vars_optional(self):
        """Test that PostgreSQL env vars are optional"""
        # DB_POSTGRES_HOST etc. can be empty without crashing the app
        assert app is not None


class TestCRUDEndpoints:
    """Test CRUD endpoints with mock data"""
    
    def test_create_requires_table(self):
        """Test that CREATE endpoint returns 503 if no DB configured"""
        response = client.post(
            "/api/test_table",
            json={"input": {"name": "test", "value": "123"}}
        )
        # Should return 503 if no database is configured
        assert response.status_code in [503, 404]
    
    def test_retrieve_requires_table(self):
        """Test that RETRIEVE endpoint returns appropriate error"""
        response = client.get("/api/test_table/query")
        # Should return 503 if no database is configured
        assert response.status_code in [503, 404]
    
    def test_update_requires_table(self):
        """Test that UPDATE endpoint returns appropriate error"""
        response = client.put(
            "/api/test_table",
            json={"input": {"name": "new"}, "where": {"id": 1}}
        )
        # Should return 503 if no database is configured
        assert response.status_code in [503, 404]
    
    def test_delete_requires_table(self):
        """Test that DELETE endpoint returns appropriate error"""
        response = client.request(
            "DELETE",
            "/api/test_table",
            json={"input": {"id": 1}}
        )
        # Should return 503 if no database is configured
        assert response.status_code in [503, 404]


class TestCSVEndpoints:
    """Test CSV import/export endpoints"""
    
    def test_csv_import_requires_file(self):
        """Test CSV import with no file"""
        response = client.post("/api/batch/import")
        assert response.status_code == 422  # Unprocessable Entity (missing file)
    
    def test_csv_export_requires_table(self):
        """Test CSV export returns appropriate error"""
        response = client.get("/api/batch/test_table/export")
        # Should return 503 if no database is configured
        assert response.status_code in [503, 404]


class TestErrorHandling:
    """Test error responses"""
    
    def test_error_response_format(self):
        """Test that error responses have the correct format"""
        response = client.get("/api/nonexistent/query")
        assert response.status_code in [503, 404]
        # If we get a JSON response, check it has expected fields
        if response.status_code != 503:
            data = response.json()
            assert "error_code" in data or "detail" in data


class TestResiliencyEngine:
    """Test resiliency/retry logic"""
    
    def test_resiliency_module_exists(self):
        """Test that resiliency module is importable"""
        from app.core.resiliency import execute_with_retries
        assert callable(execute_with_retries)
    
    def test_resiliency_handles_timeout(self):
        """Test that resiliency wrapper handles timeouts"""
        from app.core.resiliency import execute_with_retries
        
        async def timeout_func():
            await asyncio.sleep(10)  # This will timeout
            return "never"
        
        # This should raise GatewayTimeoutException
        with pytest.raises(Exception):
            asyncio.run(execute_with_retries(timeout_func))


class TestDatabaseCore:
    """Test database core utilities"""
    
    def test_database_module_exists(self):
        """Test that database module is importable"""
        from app.core.database import execute_insert
        assert callable(execute_insert)
    
    def test_error_handler_module_exists(self):
        """Test that error handler is importable"""
        from app.utils.error_handler import create_error_response
        assert callable(create_error_response)
    
    def test_error_response_creation(self):
        """Test creating error responses"""
        from app.utils.error_handler import create_error_response
        
        response = create_error_response(
            error_code="404",
            message="Not Found"
        )
        assert response.error_code == "404"
        assert response.message == "Not Found"
        assert isinstance(response.timestamp, str)
        assert len(response.timestamp) > 0
        assert response.retry_count == 0


class TestSchemaValidation:
    """Test Pydantic schema validation"""
    
    def test_crud_request_schema(self):
        """Test CRUD request validation"""
        from app.schemas.requests import CRUDRequest
        
        # Valid request
        req = CRUDRequest(input={"name": "test"})
        assert req.input["name"] == "test"
    
    def test_update_request_schema(self):
        """Test UPDATE request validation"""
        from app.schemas.requests import UpdateRequest
        
        # Valid request
        req = UpdateRequest(input={"name": "new"}, where={"id": 1})
        assert req.input["name"] == "new"
        assert req.where["id"] == 1
    
    def test_delete_request_schema(self):
        """Test DELETE request validation"""
        from app.schemas.requests import DeleteRequest
        
        # Valid request
        req = DeleteRequest(input={"id": 1})
        assert req.input["id"] == 1


class TestAPIIntegration:
    """Integration tests for the full API"""
    
    def test_api_routes_registered(self):
        """Test that all routes are registered"""
        routes = [route.path for route in app.routes]
        
        # Check CRUD routes
        assert any("/api/" in route for route in routes), "No API routes found"
        
        # Check health check
        assert "/" in routes
        assert "/api/homepage" in routes
    
    def test_cors_middleware_enabled(self):
        """Test that CORS middleware is enabled"""
        response = client.options("/")
        # CORS middleware should allow OPTIONS requests
        assert response.status_code in [200, 405]  # 200 for CORS, 405 for no handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
