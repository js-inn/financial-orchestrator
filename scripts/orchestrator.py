import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from sandbox_gateway import process_sandbox_payment

# Configuration & Environment
DB_PATH = os.getenv("DB_PATH", "db/ledger.sqlite")
STATE_JSON_PATH = os.getenv("STATE_JSON_PATH", "data/state.json")
EXPORT_PATH = os.getenv("EXPORT_PATH", "data/bureau_export.txt")

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
    """Query pending bills due soon and process them via the sandbox gateway."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    target_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime('%Y-%m-%d')
    
    cursor.execute("SELECT id, biller_name, amount, due_date FROM bills WHERE status = 'PENDING' AND due_date <= ?", (target_date,))
    pending_bills = cursor.fetchall()
    
    execution_results = []

    for bill in pending_bills:
        bill_id, biller_name, amount, due_date = bill
        print(f"Executing billing cycle for {biller_name}: ${amount} CAD (Due: {due_date})")
        
        # Execute payment through our sandbox gateway module
        gateway_result = process_sandbox_payment(bill_id, biller_name, amount)
        
        status = gateway_result["status"]
        response_data = gateway_result["data"]
            
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
    generate_metro2_record()
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

def generate_metro2_record():
    """Extract successful transactions and format them into a compliant compliance log."""
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, b.biller_name, b.amount, t.execution_timestamp, t.status 
        FROM transactions t
        JOIN bills b ON t.bill_id = b.id
        WHERE t.status = 'SUCCESS'
    """)
    records = cursor.fetchall()
    conn.close()

    if not records:
        return

    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    
    export_lines = []
    header_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    export_lines.append(f"HEADER_RECORD_OCTOPUS_CORP_{header_date}")

    for r in records:
        txn_id = str(r['id']).zfill(6)
        biller = r['biller_name'].ljust(20)[:20]
        amount_str = f"{int(r['amount'] * 100):010d}"
        timestamp = r['execution_timestamp']
        
        line = f"D|{txn_id}|{biller}|{amount_str}|PAID|{timestamp}"
        export_lines.append(line)

    export_lines.append(f"TRAILER_RECORD_COUNT_{len(records):06d}")

    with open(EXPORT_PATH, "w") as f:
        f.write("\n".join(export_lines) + "\n")
    print(f"Compliance export generated at {EXPORT_PATH}")

if __name__ == "__main__":
    print("Initializing Financial Orchestration Engine (Sandbox Mode)...")
    init_db()
    results = check_and_execute_bills()
    print(f"Execution cycle completed. Processed {len(results)} items.")
