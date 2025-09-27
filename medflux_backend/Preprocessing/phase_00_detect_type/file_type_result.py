from dataclasses import dataclass, field
from typing import Optional, Dict
from .file_type_enum import FileType

@dataclass
class FileTypeResult:
    file_path: str
    ext: str
    mime: Optional[str]
    file_type: FileType
    ocr_recommended: bool = False
    details: Dict[str, object] = field(default_factory=dict)
    confidence: float = 0.0                     # NEW: 0..1
    recommended: Dict[str, object] = field(default_factory=dict)  # NEW: suggested reader params

    def to_dict(self) -> Dict[str, object]:
        return {
            "file_path": self.file_path,
            "ext": self.ext,
            "mime": self.mime,
            "file_type": self.file_type.value,
            "ocr_recommended": self.ocr_recommended,
            "confidence": self.confidence,
            "recommended": self.recommended,
            "details": self.details,
        }
