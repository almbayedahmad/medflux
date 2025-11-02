from fastapi import APIRouter
from core.versioning import get_version_info
from core.versioning.schemas import get_schema_version

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Health check")
def health() -> dict:
    info = get_version_info()
    return {"status": "ok", "version": info.get("version"), "git_sha": info.get("git_sha")}


@router.get("/version", summary="Version info")
def version_info() -> dict:
    info = get_version_info()
    schemas = {"stage_contract": get_schema_version("stage_contract", kind="contracts")}
    return {"app": info, "schemas": schemas}
