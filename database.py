import sqlite3

DB_NAME = "restaurant.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items_summary TEXT NOT NULL,
            total_amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    sample_menu = [
        ("chicken burger", "Main", 650.0),
        ("beef burger", "Main", 750.0),
        ("veggie burger", "Main", 550.0),
        ("french fries", "Sides", 400.0),
        ("cheese pizza", "Main", 1200.0),
        ("coke", "Beverages", 150.0),
        ("iced tea", "Beverages", 200.0)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO menu (name, category, price) 
        VALUES (?, ?, ?)
    """, sample_menu)

    conn.commit()
    conn.close()
    print("Database initialized successfully with default menu.")

def fetch_menu():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM menu")
    rows = cursor.fetchall()
    conn.close()
    return {name: price for name, price in rows}

def save_order(items_summary, total_amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (items_summary, total_amount) 
        VALUES (?, ?)
    """, (items_summary, total_amount))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id

if __name__ == "__main__":
    init_db()