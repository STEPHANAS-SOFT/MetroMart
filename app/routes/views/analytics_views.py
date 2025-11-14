from fastapi import APIRouter, Depends
from ...shared.api_key_route import verify_api_key

router = APIRouter(prefix="/analytics", tags=["analytic views"])


@router.get("/admin/dashboard", dependencies=[Depends(verify_api_key)])
def get_admin_dashboard():
    # Placeholder: aggregate metrics would be computed here
    return {"total_users": 0, "total_vendors": 0, "total_orders": 0}


@router.get("/sales-report", dependencies=[Depends(verify_api_key)])
def sales_report(start_date: str = None, end_date: str = None):
    return {"report": [], "start": start_date, "end": end_date}
