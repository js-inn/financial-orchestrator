import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta
import requests

# Configuration & Environment
DB_PATH = os.getenv("DB_PATH", "db/ledger.sqlite")
STATE_JSON_PATH = os.getenv("STATE_JSON_PATH", "data/state.json")
PAYMENT_API_URL = os.getenv("PAYMENT_API_URL", "https://api.mock-payment-gateway.local/v1/execute")
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY", "")

def init_db():
    """Ensure local database and required tables exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            biller_name TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            execution_timestamp TEXT,
            status TEXT,
            response_payload TEXT,
            FOREIGN KEY (bill_id) REFERENCES bills (id)
        )
    """)
    conn.commit()
    conn.close()

def check_and_execute_bills():
    """Query pending bills due soon and process external payment triggers."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Look for bills due within the next 3 days that are still pending
    target_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime('%Y-%m-%d')
    
    cursor.execute("SELECT id, biller_name, amount, due_date FROM bills WHERE status = 'PENDING' AND due_date <= ?", (target_date,))
    pending_bills = cursor.fetchall()
    
    execution_results = []

    for bill in pending_bills:
        bill_id, biller_name, amount, due_date = bill
        print(f"Processing payment for {biller_name}: ${amount} (Due: {due_date})")
        
        payload = {
            "bill_id": bill_id,
            "biller": biller_name,
            "amount": amount,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        headers = {
            "Authorization": f"Bearer {PAYMENT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            if PAYMENT_API_URL and "mock-payment-gateway" not in PAYMENT_API_URL:
                response = requests.post(PAYMENT_API_URL, json=payload, headers=headers, timeout=15)
                response_data = response.json()
                status = "SUCCESS" if response.status_code == 200 else "FAILED"
            else:
                response_data = {"status": "simulated_success", "transaction_ref": f"TXN-{bill_id}-{int(datetime.now(timezone.utc).timestamp())}"}
                status = "SUCCESS"
                
        except Exception as e:
            response_data = {"error": str(e)}
            status = "FAILED"
            
        cursor.execute("UPDATE bills SET status = ? WHERE id = ?", (status, bill_id))
        cursor.execute(
            "INSERT INTO transactions (bill_id, execution_timestamp, status, response_payload) VALUES (?, ?, ?, ?)",
            (bill_id, datetime.now(timezone.utc).isoformat(), status, json.dumps(response_data))
        )
        conn.commit()
        
        execution_results.append({
            "bill_id": bill_id,
            "biller": biller_name,
            "amount": amount,
            "status": status,
            "response": response_data
        })

    conn.close()
    export_state_to_json()
    return execution_results

def export_state_to_json():
    """Dump active database view into an immutable JSON artifact for repo commits."""
    os.makedirs(os.path.dirname(STATE_JSON_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bills")
    bills = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM transactions")
    transactions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    state_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "bills": bills,
        "transactions": transactions
    }
    
    with open(STATE_JSON_PATH, "w") as f:
        json.dump(state_data, f, indent=2)
    print(f"State successfully exported to {STATE_JSON_PATH}")

if __name__ == "__main__":
    print("Initializing Financial Orchestration Engine...")
    init_db()
    results = check_and_execute_bills()
    print(f"Execution cycle completed. Processed {len(results)} items.")
