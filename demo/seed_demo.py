import sys
import os
import json

# Ensure the root directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import _get_connection, create_session, create_case, update_session

def seed_demo():
    print("Connecting to database...")
    
    # 2. Delete any existing session/case for GG-2026-001 or phone +919876544821
    conn = _get_connection()
    try:
        # Delete case
        conn.execute("DELETE FROM cases WHERE reference_id = ?", ("GG-2026-001",))
        # Delete session
        conn.execute("DELETE FROM sessions WHERE phone_number = ?", ("+919876544821",))
        conn.commit()
        print("Cleaned slate: deleted existing records for GG-2026-001 / +919876544821.")
    finally:
        conn.close()

    # 3. Insert a fresh session
    print("Creating fresh session...")
    session = create_session("+919876544821")
    session = update_session("+919876544821", {
        "worker_name": "Ramesh Kumar",
        "state": "open",
        "language": "en"
    })
    
    # 4. Insert a fresh case linked to that session
    print("Creating fresh case...")
    case_data = {
        "platform": "Swiggy",
        "event_type": "Account Deactivation",
        "date_occurred": "2026-06-07",
        "amount_affected": 1840.0,
        "case_status": "open",
        "filing_channel": "whatsapp",
        "reference_id": "GG-2026-001",
        "outcome": {
            "worker_phone": "+919876544821",
            "worker_name": "Ramesh Kumar",
            "city": "Bengaluru"
        }
    }
    case = create_case(session["id"], case_data)
    
    # 5. Print confirmation
    print("\n✅ Seeding complete!")
    print("--- Session ---")
    print(json.dumps(session, indent=2))
    print("\n--- Case ---")
    print(json.dumps(case, indent=2))

if __name__ == "__main__":
    seed_demo()
