import sqlite3

def run_query(sql):
    conn = sqlite3.connect("sample.db")
    cursor = conn.cursor()

    cursor.execute(sql)
    
    headers = []
    if cursor.description:
        headers = [desc[0] for desc in cursor.description]

    if sql.strip().upper().startswith("SELECT"):
        results = cursor.fetchall()
    else:
        conn.commit()
        results = "Query executed successfully."

    conn.close()
    return results, headers