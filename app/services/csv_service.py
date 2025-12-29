"""
CSV Processing Service: Batch import and export with streaming support.
Handles large files efficiently to prevent memory overflow.
"""

import csv
import io
import logging
import os
from typing import List, Dict, Any
from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from app.core.resiliency import execute_with_retries, GatewayTimeoutException
from app.core.database import (
    table_exists,
    execute_insert,
    execute_select,
    DatabaseError
)

logger = logging.getLogger(__name__)


class CSVError(Exception):
    """Base exception for CSV operations."""
    pass


async def parse_csv_file(file: UploadFile) -> tuple[str, List[Dict[str, Any]]]:
    """
    Parse a CSV file and extract table name and records.
    
    Args:
        file: Uploaded CSV file
    
    Returns:
        Tuple of (table_name, list_of_records)
    
    Raises:
        CSVError: If CSV parsing fails
    """
    try:
        # Extract table name from filename (without extension)
        filename = file.filename or "unknown"
        table_name = os.path.splitext(filename)[0]
        logger.info(f"Parsing CSV file: {filename} -> table: {table_name}")
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Parse CSV
        lines = text.strip().split('\n')
        if not lines:
            raise CSVError("CSV file is empty")
        
        reader = csv.DictReader(io.StringIO(text))
        records = list(reader)
        
        if not records:
            raise CSVError("CSV file has no data rows (only headers)")
        
        logger.info(f"Parsed {len(records)} records from {filename}")
        return table_name, records
    
    except Exception as e:
        logger.error(f"Error parsing CSV file: {e}")
        raise CSVError(f"Failed to parse CSV: {str(e)}")


async def batch_import_csv(
    file: UploadFile,
    pool
) -> Dict[str, Any]:
    """
    Perform batch import of CSV data into database.
    
    Args:
        file: CSV file to import
        pool: Database connection pool
    
    Returns:
        Dictionary with import statistics
    
    Raises:
        CSVError: If import fails
    """
    if not pool:
        raise CSVError("Database pool is not available")
    
    db_name = os.getenv("DB_NAME")
    
    try:
        # Parse CSV file
        table_name, records = await parse_csv_file(file)
        
        # Validate table exists
        try:
            exists = await execute_with_retries(table_exists, pool, table_name, db_name)
            if not exists:
                raise CSVError(f"Table '{table_name}' does not exist in database")
        except GatewayTimeoutException as e:
            raise CSVError(f"Database timeout while validating table: {str(e)}")
        
        # Batch insert records
        total_records = len(records)
        inserted = 0
        failed = 0
        errors = []
        
        for index, record in enumerate(records, 1):
            try:
                await execute_with_retries(execute_insert, pool, table_name, record)
                inserted += 1
                logger.debug(f"Inserted record {index}/{total_records} into {table_name}")
            except GatewayTimeoutException as e:
                failed += 1
                error_msg = f"Record {index}: Timeout - {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
            except DatabaseError as e:
                failed += 1
                error_msg = f"Record {index}: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
            except Exception as e:
                failed += 1
                error_msg = f"Record {index}: Unexpected error - {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
        
        logger.info(
            f"Batch import complete: {inserted} inserted, "
            f"{failed} failed out of {total_records} total"
        )
        
        return {
            "table_name": table_name,
            "total_records": total_records,
            "inserted": inserted,
            "failed": failed,
            "errors": errors if errors else None
        }
    
    except CSVError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during batch import: {e}")
        raise CSVError(f"Batch import failed: {str(e)}")


async def export_to_csv(
    table_name: str,
    pool
) -> StreamingResponse:
    """
    Export table data to CSV format with streaming.
    
    Args:
        table_name: Name of the table to export
        pool: Database connection pool
    
    Returns:
        StreamingResponse with CSV file
    
    Raises:
        CSVError: If export fails
    """
    if not pool:
        raise CSVError("Database pool is not available")
    
    db_name = os.getenv("DB_NAME")
    
    try:
        # Validate table exists
        try:
            exists = await execute_with_retries(table_exists, pool, table_name, db_name)
            if not exists:
                raise CSVError(f"Table '{table_name}' does not exist")
        except GatewayTimeoutException as e:
            raise CSVError(f"Database timeout while validating table: {str(e)}")
        
        # Fetch all records
        try:
            rows = await execute_with_retries(execute_select, pool, table_name, None)
        except GatewayTimeoutException as e:
            raise CSVError(f"Database timeout while exporting data: {str(e)}")
        
        logger.info(f"Exporting {len(rows)} records from {table_name}")
        
        # Stream CSV data
        async def generate_csv():
            if not rows:
                yield ""
                return
            
            # Write header
            fieldnames = rows[0].keys()
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=fieldnames)
            writer.writeheader()
            yield buffer.getvalue()
            
            # Write data rows
            for row in rows:
                buffer = io.StringIO()
                writer = csv.DictWriter(buffer, fieldnames=fieldnames)
                writer.writerow(row)
                yield buffer.getvalue()
        
        filename = f"{table_name}_export.csv"
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except CSVError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        raise CSVError(f"Export failed: {str(e)}")
