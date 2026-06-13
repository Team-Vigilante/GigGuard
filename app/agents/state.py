from typing import TypedDict, Optional

class GigGuardState(TypedDict):
    phone: str
    message: str
    media_url: Optional[str]
    conversation_state: str
    parsed_data: Optional[dict]
    legal_analysis: Optional[dict]
    grievance_letter: Optional[dict]
    filing_result: Optional[dict]
    confirmation_pending: bool
    case_id: Optional[str]
    error: Optional[str]
