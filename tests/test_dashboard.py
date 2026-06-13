import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
from app.db.database import create_session, create_case

client = TestClient(app)

def test_dashboard_endpoint():
    # 1. Create a dummy session and case in SQLite
    session = create_session("+910000000000")
    case_data = {
        "platform": "Swiggy",
        "event_type": "account_deactivation",
        "amount_affected": 1840,
        "filing_channel": "whatsapp"
    }
    case = create_case(session["id"], case_data)
    case_id = case["id"]
    
    # 2. Hit the dashboard endpoint
    response = client.get(f"/dashboard/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["platform"] == "Swiggy"
    print("✅ Dashboard endpoint test passed successfully!")
    print("Returned data:", data)

if __name__ == "__main__":
    test_dashboard_endpoint()
