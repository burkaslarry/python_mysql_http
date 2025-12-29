"""
CSV Routes: Import and Export endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import logging

from app.services.csv_service import batch_import_csv, export_to_csv, CSVError
from app.utils.error_handler import create_error_response, create_success_response, log_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch", tags=["csv"])


# Dependency for database pool
async def get_pool():
    from main import pool
    return pool


@router.post("/import")
async def import_csv(
    file: UploadFile = File(...),
    pool = Depends(get_pool)
):
    """
    CSV IMPORT: POST /api/batch/import
    Accepts multi-part/form-data CSV files.
    Uses filename (minus extension) as table name.
    Performs batch inserts with error tracking.
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    if not file.filename or not file.filename.endswith('.csv'):
        response = create_error_response(
            error_code="400",
            message="File must be a CSV file"
        )
        raise HTTPException(status_code=400, detail=response.model_dump())
    
    try:
        import_stats = await batch_import_csv(file, pool)
        response = create_success_response(
            message="CSV import completed",
            data=import_stats
        )
        return response.model_dump()
    except CSVError as e:
        response = create_error_response(
            error_code="400",
            message=f"CSV import error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during CSV import"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())


@router.get("/{table_name}/export")
async def export_csv(
    table_name: str,
    pool = Depends(get_pool)
):
    """
    CSV EXPORT: GET /api/batch/:tableName/export
    Exports all records from the specified table as a downloadable CSV file.
    Uses streaming to handle large datasets efficiently.
    """
    if not pool:
        response = create_error_response(
            error_code="503",
            message="Database not available"
        )
        raise HTTPException(status_code=503, detail=response.model_dump())
    
    try:
        return await export_to_csv(table_name, pool)
    except CSVError as e:
        response = create_error_response(
            error_code="400",
            message=f"CSV export error: {str(e)}"
        )
        log_error("400", str(e), e)
        raise HTTPException(status_code=400, detail=response.model_dump())
    except Exception as e:
        response = create_error_response(
            error_code="500",
            message="Unexpected error during CSV export"
        )
        log_error("500", str(e), e)
        raise HTTPException(status_code=500, detail=response.model_dump())
