from pydantic import BaseModel
from typing import Any, Optional

class ValidationIssue(BaseModel):
    code: str
    message: str
    category: str
    sheet: Optional[str] = None
    cell: Optional[str] = None
    expected: Any = None
    actual: Any = None

class FileValidationResult(BaseModel):
    filename: str
    status: str
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
