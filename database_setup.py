import sqlite3

conn = sqlite3.connect("sample.db")
cursor = conn.cursor()

# Set up customers
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT
)
""")
cursor.execute("INSERT INTO customers(name,city) VALUES('Rahul','Hyderabad')")
cursor.execute("INSERT INTO customers(name,city) VALUES('Amit','Delhi')")
cursor.execute("INSERT INTO customers(name,city) VALUES('Sita','Hyderabad')")

# Set up orders
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product TEXT,
    price REAL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
""")
cursor.execute("INSERT INTO orders(customer_id, product, price) VALUES(1, 'Laptop', 1200.00)")
cursor.execute("INSERT INTO orders(customer_id, product, price) VALUES(1, 'Mouse', 25.00)")
cursor.execute("INSERT INTO orders(customer_id, product, price) VALUES(3, 'Phone', 800.00)")

conn.commit()
conn.close()

print("Database created and seeded successfully with customers and orders tables.")