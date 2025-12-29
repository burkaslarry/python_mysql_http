"""
Database Utility Module: Query execution, validation, and table schema reflection.
Handles parameterized queries to prevent SQL injection.
"""

import logging
import aiomysql
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class TableNotFoundError(DatabaseError):
    """Raised when a table does not exist."""
    pass


class InvalidOperationError(DatabaseError):
    """Raised when an invalid database operation is attempted."""
    pass


async def table_exists(pool: aiomysql.Pool, table_name: str, db_name: str) -> bool:
    """
    Check if a table exists in the information schema.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table to check
        db_name: Name of the database
    
    Returns:
        True if table exists, False otherwise
    """
    if not pool:
        logger.warning("Database pool is None. Cannot check table existence.")
        return False
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                """
                await cursor.execute(query, (db_name, table_name))
                result = await cursor.fetchone()
                exists = result[0] > 0
                logger.debug(f"Table '{table_name}' existence check: {exists}")
                return exists
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        raise DatabaseError(f"Failed to check table existence: {str(e)}")


async def get_table_columns(pool: aiomysql.Pool, table_name: str, db_name: str) -> List[str]:
    """
    Get all column names from a table.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table
        db_name: Name of the database
    
    Returns:
        List of column names
    """
    if not pool:
        logger.warning("Database pool is None. Cannot fetch table columns.")
        return []
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """
                await cursor.execute(query, (db_name, table_name))
                results = await cursor.fetchall()
                columns = [row[0] for row in results]
                logger.debug(f"Columns for '{table_name}': {columns}")
                return columns
    except Exception as e:
        logger.error(f"Error fetching table columns: {e}")
        raise DatabaseError(f"Failed to fetch table columns: {str(e)}")


def build_where_clause(where_dict: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Build a WHERE clause from a dictionary of conditions.
    
    Args:
        where_dict: Dictionary with column names as keys and filter values
    
    Returns:
        Tuple of (WHERE clause string, list of values for parameterized query)
    """
    if not where_dict:
        return "", []
    
    conditions = []
    values = []
    
    for column, value in where_dict.items():
        if value is None:
            conditions.append(f"`{column}` IS NULL")
        else:
            conditions.append(f"`{column}` = %s")
            values.append(value)
    
    where_clause = " AND ".join(conditions)
    logger.debug(f"WHERE clause: {where_clause}")
    return where_clause, values


def build_set_clause(data_dict: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Build a SET clause for UPDATE statements.
    
    Args:
        data_dict: Dictionary with column names and new values
    
    Returns:
        Tuple of (SET clause string, list of values for parameterized query)
    """
    if not data_dict:
        raise InvalidOperationError("UPDATE requires at least one column to update")
    
    conditions = []
    values = []
    
    for column, value in data_dict.items():
        conditions.append(f"`{column}` = %s")
        values.append(value)
    
    set_clause = ", ".join(conditions)
    logger.debug(f"SET clause: {set_clause}")
    return set_clause, values


async def execute_insert(
    pool: aiomysql.Pool,
    table_name: str,
    data: Dict[str, Any]
) -> int:
    """
    Execute an INSERT statement with parameterized query.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table
        data: Dictionary with column names and values
    
    Returns:
        Number of rows affected
    """
    if not data:
        raise InvalidOperationError("INSERT requires at least one column and value")
    
    columns = ", ".join([f"`{col}`" for col in data.keys()])
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())
    
    query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)
                await conn.commit()
                rows_affected = cursor.rowcount
                logger.info(f"Inserted {rows_affected} rows into '{table_name}'")
                return rows_affected
    except Exception as e:
        logger.error(f"Error inserting into '{table_name}': {e}")
        raise DatabaseError(f"Failed to insert data: {str(e)}")


async def execute_select(
    pool: aiomysql.Pool,
    table_name: str,
    where_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a SELECT statement with optional WHERE conditions.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table
        where_dict: Optional dictionary with WHERE conditions
    
    Returns:
        List of dictionaries representing rows
    """
    where_clause, where_values = build_where_clause(where_dict or {})
    
    if where_clause:
        query = f"SELECT * FROM `{table_name}` WHERE {where_clause}"
    else:
        query = f"SELECT * FROM `{table_name}`"
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, where_values)
                rows = await cursor.fetchall()
                logger.info(f"Selected {len(rows)} rows from '{table_name}'")
                return rows
    except Exception as e:
        logger.error(f"Error selecting from '{table_name}': {e}")
        raise DatabaseError(f"Failed to select data: {str(e)}")


async def execute_update(
    pool: aiomysql.Pool,
    table_name: str,
    data: Dict[str, Any],
    where_dict: Dict[str, Any]
) -> int:
    """
    Execute an UPDATE statement with parameterized query.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table
        data: Dictionary with new column values
        where_dict: Dictionary with WHERE conditions
    
    Returns:
        Number of rows affected
    """
    set_clause, set_values = build_set_clause(data)
    where_clause, where_values = build_where_clause(where_dict)
    
    if not where_clause:
        raise InvalidOperationError("UPDATE requires WHERE conditions for safety")
    
    query = f"UPDATE `{table_name}` SET {set_clause} WHERE {where_clause}"
    all_values = set_values + where_values
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, all_values)
                await conn.commit()
                rows_affected = cursor.rowcount
                logger.info(f"Updated {rows_affected} rows in '{table_name}'")
                return rows_affected
    except Exception as e:
        logger.error(f"Error updating '{table_name}': {e}")
        raise DatabaseError(f"Failed to update data: {str(e)}")


async def execute_delete(
    pool: aiomysql.Pool,
    table_name: str,
    where_dict: Dict[str, Any]
) -> int:
    """
    Execute a DELETE statement with parameterized query.
    
    Args:
        pool: Database connection pool
        table_name: Name of the table
        where_dict: Dictionary with WHERE conditions
    
    Returns:
        Number of rows affected
    """
    where_clause, where_values = build_where_clause(where_dict)
    
    if not where_clause:
        raise InvalidOperationError("DELETE requires WHERE conditions for safety")
    
    query = f"DELETE FROM `{table_name}` WHERE {where_clause}"
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, where_values)
                await conn.commit()
                rows_affected = cursor.rowcount
                logger.info(f"Deleted {rows_affected} rows from '{table_name}'")
                return rows_affected
    except Exception as e:
        logger.error(f"Error deleting from '{table_name}': {e}")
        raise DatabaseError(f"Failed to delete data: {str(e)}")
