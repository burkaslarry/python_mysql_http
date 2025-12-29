"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class CRUDRequest(BaseModel):
    """
    Base request schema for CRUD operations.
    Strict format: { "input": { ...data } }
    """
    input: Dict[str, Any]


class UpdateRequest(BaseModel):
    """
    Update request schema: { "input": { ...new_values }, "where": { ...conditions } }
    """
    input: Dict[str, Any]
    where: Dict[str, Any]


class DeleteRequest(BaseModel):
    """
    Delete request schema: { "input": { ...WHERE_conditions } }
    """
    input: Dict[str, Any]
