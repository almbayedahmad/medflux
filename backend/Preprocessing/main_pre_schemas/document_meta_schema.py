"""
Module: document_meta_schema

Layer: MAIN (Preprocessing)

Role: Shared document metadata schema across all phases

Reused by: ALL phases

Notes: Version 1.0.0
"""

from typing import TypedDict, NotRequired

class DocumentMeta(TypedDict):
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    created_at: NotRequired[str]
    modified_at: NotRequired[str]
