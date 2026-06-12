from fastapi import APIRouter, HTTPException
from app.db.database import get_case, get_case_by_reference

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{case_id}")
def get_case_dashboard(case_id: str):
    """
    Retrieve case details from SQLite for the dashboard.
    """
    case_data = get_case(case_id)
    if not case_data:
        case_data = get_case_by_reference(case_id)
        
    if not case_data:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_data
