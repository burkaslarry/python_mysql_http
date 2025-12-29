"""
Dynamic CRUD Routes: Table-agnostic endpoints with resiliency wrapper.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import os
import logging

from app.core.resiliency import execute_with_retries, GatewayTimeoutException
from app.core.database import (
    table_exists,
    execute_insert,
    execute_select,
    execute_update,
    execute_delete,
    DatabaseError,
    InvalidOperationError
)
from app.schemas.requests import CRUDRequest, UpdateRequest, DeleteRequest
from app.utils.error_handler import create_error_response, create_success_response, log_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["crud"])

# Dependency for database pool
async def get_pool():
    from main import pool
    return pool


@router.post("/{table_name}")
async def create_record(
    table_name: str,
    request: CRUDRequest,
    pool = Depends(get_pool)
):
    """
    CREATE: POST /api/:tableName
    Accepts { "input": { ...data } } and inserts into the specified table.
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    db_name = os.getenv("DB_NAME")
    
    # Validate table exists
    try:
        exists = await execute_with_retries(table_exists, pool, table_name, db_name)
        if not exists:
            response = create_error_response(
                error_code="404",
                message=f"Table '{table_name}' does not exist"
            )
            raise HTTPException(status_code=404, detail=response.model_dump())
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Database timeout during table validation",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Error validating table"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
    
    # Execute insert with retry
    try:
        rows_affected = await execute_with_retries(
            execute_insert, pool, table_name, request.input
        )
        response = create_success_response(
            message=f"Record inserted successfully",
            data={"rows_affected": rows_affected}
        )
        return response.model_dump()
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Insert operation timed out",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except DatabaseError as e:
        response = create_error_response(
            error_code="400",
            message=f"Database error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during insert"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())


@router.get("/{table_name}/query")
async def retrieve_records(
    table_name: str,
    pool = Depends(get_pool)
):
    """
    RETRIEVE: GET /api/:tableName/query
    Accepts { "input": { ...WHERE_conditions } } for filtering.
    If no input is provided in the request, retrieves all records.
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    db_name = os.getenv("DB_NAME")
    
    # Validate table exists
    try:
        exists = await execute_with_retries(table_exists, pool, table_name, db_name)
        if not exists:
            response = create_error_response(
                error_code="404",
                message=f"Table '{table_name}' does not exist"
            )
            raise HTTPException(status_code=404, detail=response.model_dump())
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Database timeout during table validation",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Error validating table"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
    
    # Execute select with retry (no WHERE conditions)
    try:
        rows = await execute_with_retries(execute_select, pool, table_name, None)
        response = create_success_response(
            message=f"Retrieved {len(rows)} record(s)",
            data=rows
        )
        return response.model_dump()
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Select operation timed out",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except DatabaseError as e:
        response = create_error_response(
            error_code="400",
            message=f"Database error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during select"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())


@router.post("/{table_name}/query")
async def retrieve_records_with_filter(
    table_name: str,
    request: CRUDRequest,
    pool = Depends(get_pool)
):
    """
    RETRIEVE with WHERE: POST /api/:tableName/query
    Accepts { "input": { ...WHERE_conditions } } for filtering.
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    db_name = os.getenv("DB_NAME")
    
    # Validate table exists
    try:
        exists = await execute_with_retries(table_exists, pool, table_name, db_name)
        if not exists:
            response = create_error_response(
                error_code="404",
                message=f"Table '{table_name}' does not exist"
            )
            raise HTTPException(status_code=404, detail=response.model_dump())
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Database timeout during table validation",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Error validating table"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
    
    # Execute select with retry and WHERE conditions
    try:
        rows = await execute_with_retries(
            execute_select, pool, table_name, request.input
        )
        response = create_success_response(
            message=f"Retrieved {len(rows)} record(s)",
            data=rows
        )
        return response.model_dump()
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Select operation timed out",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except DatabaseError as e:
        response = create_error_response(
            error_code="400",
            message=f"Database error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during select"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())


@router.put("/{table_name}")
async def update_record(
    table_name: str,
    request: UpdateRequest,
    pool = Depends(get_pool)
):
    """
    UPDATE: PUT /api/:tableName
    Accepts { "input": { ...new_values }, "where": { ...conditions } }
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    db_name = os.getenv("DB_NAME")
    
    # Validate table exists
    try:
        exists = await execute_with_retries(table_exists, pool, table_name, db_name)
        if not exists:
            response = create_error_response(
                error_code="404",
                message=f"Table '{table_name}' does not exist"
            )
            raise HTTPException(status_code=404, detail=response.model_dump())
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Database timeout during table validation",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Error validating table"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
    
    # Execute update with retry
    try:
        rows_affected = await execute_with_retries(
            execute_update, pool, table_name, request.input, request.where
        )
        response = create_success_response(
            message=f"Record updated successfully",
            data={"rows_affected": rows_affected}
        )
        return response.model_dump()
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Update operation timed out",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except InvalidOperationError as e:
        response = create_error_response(
            error_code="400",
            message=f"Invalid operation: {str(e)}"
        )
        log_error("400", str(e))
        raise HTTPException(status_code=400, detail=response.model_dump())
    except DatabaseError as e:
        response = create_error_response(
            error_code="400",
            message=f"Database error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during update"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())


@router.delete("/{table_name}")
async def delete_record(
    table_name: str,
    request: DeleteRequest,
    pool = Depends(get_pool)
):
    """
    DELETE: DELETE /api/:tableName
    Accepts { "input": { ...WHERE_conditions } }
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    db_name = os.getenv("DB_NAME")
    
    # Validate table exists
    try:
        exists = await execute_with_retries(table_exists, pool, table_name, db_name)
        if not exists:
            response = create_error_response(
                error_code="404",
                message=f"Table '{table_name}' does not exist"
            )
            raise HTTPException(status_code=404, detail=response.model_dump())
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Database timeout during table validation",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Error validating table"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
    
    # Execute delete with retry
    try:
        rows_affected = await execute_with_retries(
            execute_delete, pool, table_name, request.input
        )
        response = create_success_response(
            message=f"Record deleted successfully",
            data={"rows_affected": rows_affected}
        )
        return response.model_dump()
    except GatewayTimeoutException as e:
        response = create_error_response(
            error_code="504",
            message="Delete operation timed out",
            retry_count=e.retry_count
        )
        log_error("504", str(e))
        raise HTTPException(status_code=504, detail=response.model_dump())
    except InvalidOperationError as e:
        response = create_error_response(
            error_code="400",
            message=f"Invalid operation: {str(e)}"
        )
        log_error("400", str(e))
        raise HTTPException(status_code=400, detail=response.model_dump())
    except DatabaseError as e:
        response = create_error_response(
            error_code="400",
            message=f"Database error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during delete"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
