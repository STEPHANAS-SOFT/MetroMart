from fastapi import APIRouter, Depends
from ...shared.api_key_route import verify_api_key

router = APIRouter(prefix="/system", tags=["system views"])


@router.get("/health", dependencies=[Depends(verify_api_key)])
def detailed_health():
    # Placeholder: perform DB checks, external service checks, etc.
    return {"status": "healthy", "db": "ok", "services": {}}


@router.get("/metrics", dependencies=[Depends(verify_api_key)])
def metrics():
    # Placeholder for metrics
    return {"uptime": 0, "requests": 0}
