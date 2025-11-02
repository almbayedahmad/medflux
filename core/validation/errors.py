from __future__ import annotations

from typing import Any, Dict, Optional


class ValidationError(Exception):
    """Raised when payload validation fails.

    Attributes:
        code: Stable error code (e.g., VL-E001 for input, VL-E002 for output)
        details: Optional structured details to aid debugging/telemetry
    """

    def __init__(self, message: str, code: str = "VL-E000", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"message": str(self), "code": self.code, "details": self.details}
