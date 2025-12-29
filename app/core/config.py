"""
Database Configuration Module
Supports MySQL and PostgreSQL connections
"""

import os
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class DatabaseConfig:
    """Database configuration"""
    
    # MySQL Configuration
    MYSQL_HOST: Optional[str] = os.getenv("DB_HOST")
    MYSQL_PORT: int = int(os.getenv("DB_PORT", "3306"))
    MYSQL_USER: Optional[str] = os.getenv("DB_USER")
    MYSQL_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    MYSQL_DATABASE: Optional[str] = os.getenv("DB_NAME")
    
    # PostgreSQL Configuration
    POSTGRES_HOST: Optional[str] = os.getenv("DB_POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("DB_POSTGRES_PORT", "5432"))
    POSTGRES_USER: Optional[str] = os.getenv("DB_POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("DB_POSTGRES_PASSWORD")
    POSTGRES_DATABASE: Optional[str] = os.getenv("DB_POSTGRES_NAME")
    
    @classmethod
    def is_mysql_configured(cls) -> bool:
        """Check if MySQL is configured"""
        return all([
            cls.MYSQL_HOST,
            cls.MYSQL_USER,
            cls.MYSQL_PASSWORD,
            cls.MYSQL_DATABASE
        ])
    
    @classmethod
    def is_postgresql_configured(cls) -> bool:
        """Check if PostgreSQL is configured"""
        return all([
            cls.POSTGRES_HOST,
            cls.POSTGRES_USER,
            cls.POSTGRES_PASSWORD,
            cls.POSTGRES_DATABASE
        ])
    
    @classmethod
    def get_active_database_type(cls) -> Optional[DatabaseType]:
        """Get the active database type"""
        if cls.is_mysql_configured():
            return DatabaseType.MYSQL
        elif cls.is_postgresql_configured():
            return DatabaseType.POSTGRESQL
        return None
    
    @classmethod
    def log_configuration(cls):
        """Log the current configuration"""
        mysql_status = "CONFIGURED" if cls.is_mysql_configured() else "NOT CONFIGURED"
        postgres_status = "CONFIGURED" if cls.is_postgresql_configured() else "NOT CONFIGURED"
        
        logger.info(f"MySQL Status: {mysql_status}")
        logger.info(f"PostgreSQL Status: {postgres_status}")
        
        active = cls.get_active_database_type()
        logger.info(f"Active Database: {active.value if active else 'NONE'}")


# MySQL connection string
def get_mysql_url() -> Optional[str]:
    """Get MySQL connection URL"""
    if not DatabaseConfig.is_mysql_configured():
        return None
    
    return (
        f"mysql+aiomysql://{DatabaseConfig.MYSQL_USER}:"
        f"{DatabaseConfig.MYSQL_PASSWORD}@{DatabaseConfig.MYSQL_HOST}:"
        f"{DatabaseConfig.MYSQL_PORT}/{DatabaseConfig.MYSQL_DATABASE}"
    )


# PostgreSQL connection string
def get_postgresql_url() -> Optional[str]:
    """Get PostgreSQL connection URL"""
    if not DatabaseConfig.is_postgresql_configured():
        return None
    
    return (
        f"postgresql+asyncpg://{DatabaseConfig.POSTGRES_USER}:"
        f"{DatabaseConfig.POSTGRES_PASSWORD}@{DatabaseConfig.POSTGRES_HOST}:"
        f"{DatabaseConfig.POSTGRES_PORT}/{DatabaseConfig.POSTGRES_DATABASE}"
    )
