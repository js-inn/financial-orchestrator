import sqlite3
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect('db/ledger.sqlite')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        biller_name TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING'
    )
''')

due_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
cursor.execute(
    'INSERT INTO bills (biller_name, amount, due_date, status) VALUES (?, ?, ?, ?)',
    ('Test Utility Provider', 75.50, due_date, 'PENDING')
)

conn.commit()
conn.close()
print('Fresh test bill seeded successfully!')
