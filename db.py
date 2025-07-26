import sqlite3
from datetime import datetime
import pandas as pd

DB_FILE = "fruit_packing.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS dc_entries (
            dc_entry_number TEXT UNIQUE,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dc_rows (
            dc_entry_number TEXT,
            item TEXT,
            dozen INTEGER,
            boxes REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dc_delivery_details (
            dc_entry_number TEXT,
            item TEXT,
            boxes REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_dc_entry(dc_entry_number, rows):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT INTO dc_entries (dc_entry_number, created_at) VALUES (?, ?)",
              (dc_entry_number, datetime.now().isoformat()))

    for row in rows:
        c.execute(
            "INSERT INTO dc_rows (dc_entry_number, item, dozen, boxes) VALUES (?, ?, ?, ?)",
            (dc_entry_number, row['Item'], row['Dozen'], row['Boxes'])
        )

    conn.commit()
    conn.close()

def fetch_dc_entry(dc_entry_number):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT r.item, r.dozen, r.boxes 
        FROM 
        dc_rows r
        WHERE r.dc_entry_number = ?
    ''', (dc_entry_number,))
    rows = c.fetchall()
    conn.close()
    return [{"Item": item, "Dozen": dozen, "Boxes": boxes} for item, dozen, boxes in rows]

def add_dc_delivery_details(dc_entry_number, date, item, boxes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO dc_delivery_details (dc_entry_number, item, boxes, date) VALUES (?, ?, ?, ?)",
        (dc_entry_number, item, boxes, date.isoformat())
    )
    conn.commit()
    conn.close()

def get_dc_delivery_details(dc_entry_number):
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT date, item as Item_Name, boxes as Expected_Box 
        FROM dc_delivery_details
        WHERE dc_entry_number = ?
        ORDER BY item
    """
    df = pd.read_sql_query(query, conn, params=(dc_entry_number,))
    conn.close()
    return df


def get_dc_cumulative_delivery_details(dc_entry_number):
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT item as Item, SUM(boxes) as total_delivered
        FROM dc_delivery_details
        WHERE dc_entry_number = ?
        GROUP BY item
        ORDER BY item
    """
    df = pd.read_sql_query(query, conn, params=(dc_entry_number,))
    conn.close()
    return df

def get_dc_delivery_details_with_date_filter(from_date, to_date):
    conn = sqlite3.connect(DB_FILE)
    query = '''
            SELECT dc_entry_number, date, item, boxes
            FROM dc_delivery_details
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
    '''
    df = pd.read_sql_query(query, conn, params=(from_date.isoformat(), to_date.isoformat()))
    # Convert date column to dd-mm-yyyy format
    df["date"] = pd.to_datetime(df["date"]).dt.strftime('%d-%m-%Y')
    conn.close()
    return df