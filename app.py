import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from sql_generator import generate_sql

load_dotenv()

app = Flask(__name__, template_folder="templates")
CORS(app)

# Auto-initialize database on startup if it's missing
if not os.path.exists("sample.db"):
    try:
        conn = sqlite3.connect("sample.db")
        cursor = conn.cursor()
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
        print("Database auto-initialized on startup.")
    except Exception as e:
        print(f"Error auto-initializing database: {e}")

def reset_db():
    conn = sqlite3.connect("sample.db")
    cursor = conn.cursor()
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

def execute_sql(sql):
    conn = sqlite3.connect("sample.db")
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        # Check if it's a query that returns rows (SELECT)
        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()
            return {
                "success": True, 
                "type": "select",
                "rows": rows, 
                "headers": headers,
                "message": f"Found {len(rows)} result(s)."
            }
        else:
            conn.commit()
            conn.close()
            return {
                "success": True, 
                "type": "mutation",
                "message": "Query executed successfully."
            }
    except Exception as e:
        conn.close()
        return {
            "success": False, 
            "error": str(e)
        }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/query", methods=["POST"])
def process_query():
    data = request.get_json() or {}
    user_query = data.get("query", "").strip()
    
    if not user_query:
        return jsonify({"success": False, "error": "Query text is required."}), 400

    try:
        sql = generate_sql(user_query)
        print(f"USER QUERY: '{user_query}'")
        print(f"GENERATED SQL: '{sql}'")
        if not sql:
            return jsonify({
                "success": False, 
                "error": "Could not generate SQL for the given request."
            }), 400
            
        result = execute_sql(sql)
        print(f"RESULT: {result}")
        result["sql"] = sql
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset_database():
    try:
        reset_db()
        return jsonify({"success": True, "message": "Database reset to sample state successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Ensure database is set up on run
    try:
        reset_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        
    app.run(host="0.0.0.0", port=5000, debug=True)
