"""
Initialize the test SQLite database with a sample e-commerce schema and data.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test_store.db")


def init_test_database():
    """Create and populate the test database if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Schema ---
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            city        TEXT,
            country     TEXT,
            joined_at   TEXT    DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            order_date  TEXT    DEFAULT (date('now')),
            status      TEXT    CHECK(status IN ('pending','confirmed','shipped','delivered','cancelled')),
            total       REAL    NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER REFERENCES orders(id),
            product_id  INTEGER REFERENCES products(id),
            quantity    INTEGER NOT NULL,
            unit_price  REAL    NOT NULL
        );
    """)

    # Only insert if tables are empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return DB_PATH

    # --- Categories ---
    categories = ["Electronics", "Clothing", "Books", "Sports", "Home & Garden"]
    cursor.executemany("INSERT INTO categories (name) VALUES (?)", [(c,) for c in categories])

    # --- Customers ---
    customers = [
        ("Alice Martin",    "alice@email.com",   "Paris",      "France"),
        ("Bob Smith",       "bob@email.com",     "London",     "UK"),
        ("Carlos Ruiz",     "carlos@email.com",  "Madrid",     "Spain"),
        ("Diana Prince",    "diana@email.com",   "New York",   "USA"),
        ("Erik Larsson",    "erik@email.com",    "Stockholm",  "Sweden"),
        ("Fatima Zahra",    "fatima@email.com",  "Casablanca", "Morocco"),
        ("George Brown",    "george@email.com",  "Sydney",     "Australia"),
        ("Hannah Müller",   "hannah@email.com",  "Berlin",     "Germany"),
        ("Ivan Petrov",     "ivan@email.com",    "Moscow",     "Russia"),
        ("Julia Santos",    "julia@email.com",   "São Paulo",  "Brazil"),
    ]
    cursor.executemany(
        "INSERT INTO customers (name, email, city, country) VALUES (?,?,?,?)", customers
    )

    # --- Products ---
    products = [
        ("iPhone 15 Pro",        1, 1199.99, 50),
        ("Samsung Galaxy S24",   1,  999.99, 35),
        ("MacBook Air M3",       1, 1499.00, 20),
        ("Sony WH-1000XM5",      1,  349.99, 80),
        ("Levi's 501 Jeans",     2,   89.99, 200),
        ("Nike Air Max 2024",    2,  129.99, 150),
        ("Python Crash Course",  3,   39.99, 300),
        ("Clean Code",           3,   44.99, 250),
        ("Yoga Mat Pro",         4,   49.99, 100),
        ("Running Shoes X",      4,  159.99, 90),
        ("Coffee Maker Deluxe",  5,   89.99, 60),
        ("LED Desk Lamp",        5,   34.99, 120),
    ]
    cursor.executemany(
        "INSERT INTO products (name, category_id, price, stock) VALUES (?,?,?,?)", products
    )

    # --- Orders ---
    orders = [
        (1, "2024-01-15", "delivered",  1549.98),
        (2, "2024-02-10", "delivered",   349.99),
        (3, "2024-02-20", "shipped",    1089.98),
        (4, "2024-03-05", "confirmed",   254.97),
        (5, "2024-03-12", "delivered",   999.99),
        (1, "2024-04-01", "pending",     469.98),
        (6, "2024-04-15", "delivered",   219.98),
        (7, "2024-05-03", "cancelled",  1499.00),
        (8, "2024-05-20", "shipped",     209.98),
        (9, "2024-06-08", "delivered",   474.97),
        (10,"2024-06-25", "pending",    1329.98),
        (2, "2024-07-01", "confirmed",   209.98),
    ]
    cursor.executemany(
        "INSERT INTO orders (customer_id, order_date, status, total) VALUES (?,?,?,?)", orders
    )

    # --- Order Items ---
    order_items = [
        (1, 3,  1, 1499.00), (1, 12, 1,   34.99),   # Order 1
        (2, 4,  1,  349.99),                          # Order 2
        (3, 1,  1, 1199.99), (3, 7,  1,   39.99),   # Order 3 (approx)
        (4, 5,  1,   89.99), (4, 8,  1,   44.99), (4, 12, 1, 34.99),  # Order 4
        (5, 2,  1,  999.99),                          # Order 5
        (6, 4,  1,  349.99), (6, 9,  1,   49.99), (6, 12, 1, 34.99),  # Order 6
        (7, 5,  1,   89.99), (7, 7,  1,   39.99), (7, 8,  1,  44.99),  # Order 7
        (8, 3,  1, 1499.00),                          # Order 8
        (9, 5,  1,   89.99), (9, 6,  1,  129.99),   # Order 9
        (10,1,  1, 1199.99), (10,7,  2,   39.99), (10,12,1,  34.99),  # Order 10
        (11,1,  1, 1199.99), (11,7,  1,   39.99), (11,8, 1,  44.99),  # Order 11
        (12,6,  1,  159.99), (12,11, 1,   89.99), (12,7, 1,  39.99),  # Order 12
    ]
    cursor.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
        order_items
    )

    conn.commit()
    conn.close()
    return DB_PATH


def get_db_path():
    return DB_PATH


if __name__ == "__main__":
    path = init_test_database()
    print(f"✅ Test database initialized at: {path}")
