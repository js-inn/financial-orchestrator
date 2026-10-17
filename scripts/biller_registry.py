import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "db/ledger.sqlite")

# Predefined sole-proprietor operational billers and vendors
DEFAULT_BILLERS = [
    ("Hydro Edmonton Utility", 145.80, "UTILITIES"),
    ("Edmonton Telecommunications", 89.50, "TELECOM"),
    ("Cloud Infrastructure Provider", 45.00, "SOFTWARE"),
    ("Co-working Space Desk Fee", 250.00, "OPERATIONS")
]

def init_biller_table():
    """Ensure the billers metadata table exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS billers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            biller_name TEXT UNIQUE NOT NULL,
            default_amount REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def seed_billers():
    """Populate default sole-proprietor billers into the registry."""
    init_biller_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for name, amount, category in DEFAULT_BILLERS:
        cursor.execute("""
            INSERT OR IGNORE INTO billers (biller_name, default_amount, category)
            VALUES (?, ?, ?)
        """, (name, amount, category))
        
    conn.commit()
    conn.close()
    print("[REGISTRY] Sole-proprietor biller registry synchronized.")

if __name__ == "__main__":
    seed_billers()
