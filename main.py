import os
import json
import sqlite3
import speech_recognition as sr
from dotenv import load_dotenv
from sql_generator import generate_sql
from database_query import run_query

# Load environment variables
load_dotenv()

HISTORY_FILE = ".query_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                return data.get("queries", []), data.get("sql", [])
        except Exception:
            pass
    return [], []

def save_history(queries, sql_list):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({"queries": queries, "sql": sql_list}, f, indent=4)
    except Exception:
        pass

def print_table(headers, rows):
    if not headers or not rows:
        print("\n[Empty result set]")
        return
        
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val if val is not None else "")))
            
    # Format line separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    # Print table
    print(separator)
    print("|" + "|".join(f" {h.upper():<{col_widths[idx]}} " for idx, h in enumerate(headers)) + "|")
    print(separator)
    for row in rows:
        print("|" + "|".join(f" {str(val if val is not None else ''):<{col_widths[idx]}} " for idx, val in enumerate(row)) + "|")
    print(separator)

def reset_database():
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
    conn.commit()
    conn.close()
    # Also reset history file
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    print("\nDatabase reset to initial mock records, and query histories cleared.")

def record_and_transcribe():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("\nListening... Speak your database request in plain English.")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            print("Processing voice...")
            text = recognizer.recognize_google(audio)
            return text.strip()
    except sr.UnknownValueError:
        print("\n[Error] Speech recognition could not understand the audio.")
    except sr.RequestError:
        print("\n[Error] Speech recognition service is currently unavailable.")
    except Exception as e:
        print(f"\n[Microphone Error] Could not access microphone: {e}")
        print("Falling back to text input mode.")
    return None

def process_query_flow(query_text, recent_queries, recent_sql):
    if not query_text:
        return
        
    print(f"\nCaptured Query: \"{query_text}\"")
    
    # Prompt to verify or edit
    while True:
        choice = input("Did I get that right? (y / n / edit): ").strip().lower()
        if choice in ["y", "yes", ""]:
            break
        elif choice in ["n", "no", "cancel"]:
            print("Operation cancelled.")
            return
        elif choice in ["e", "edit"]:
            query_text = input("Type corrected query: ").strip()
            print(f"\nUpdated Query: \"{query_text}\"")
        else:
            print("Invalid option. Please enter 'y', 'n', or 'edit'.")

    # Generate SQL
    print("Generating SQL...")
    try:
        sql = generate_sql(query_text)
        if not sql:
            print("\n[Error] Could not translate query to SQL.")
            return
    except Exception as e:
        print(f"\n[Error] SQL Generation failed: {e}")
        return

    print(f"Developer SQL: {sql}")
    
    # Execute SQL
    try:
        result, headers = run_query(sql)
        
        # Display Results
        if isinstance(result, list):
            print_table(headers, result)
        else:
            print(f"\nStatus: {result}")
            print("\nUpdated Customers List:")
            updated_res, updated_headers = run_query("SELECT * FROM customers;")
            print_table(updated_headers, updated_res)
            
        # Update and persist history lists
        recent_queries = [q for q in recent_queries if q != query_text]
        recent_queries.insert(0, query_text)
        recent_queries = recent_queries[:5]
        
        recent_sql = [s for s in recent_sql if s != sql]
        recent_sql.insert(0, sql)
        recent_sql = recent_sql[:5]
        
        save_history(recent_queries, recent_sql)
        
    except Exception as e:
        print(f"\n[Database Error] Failed to execute SQL: {e}")

def main():
    recent_queries, recent_sql = load_history()
    
    while True:
        print("\n=========================================")
        print("   Plain English Database Assistant 🎙️    ")
        print("=========================================")
        print("[1] Voice Query (Microphone)")
        print("[2] Text Query (Type)")
        print("[3] View Recent Queries")
        print("[4] Reset Database & Logs")
        print("[5] Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        # Reload history to keep in sync
        recent_queries, recent_sql = load_history()
        
        if choice == "1":
            text = record_and_transcribe()
            if text:
                process_query_flow(text, recent_queries, recent_sql)
        elif choice == "2":
            text = input("\nEnter query in plain English: ").strip()
            if text:
                process_query_flow(text, recent_queries, recent_sql)
        elif choice == "3":
            print("\n--- Recent Plain English Queries (Last 5) ---")
            if not recent_queries:
                print("[No queries run yet]")
            else:
                for idx, q in enumerate(recent_queries, 1):
                    print(f"  {idx}. \"{q}\"")
                    
            print("\n--- Recent SQL Queries (Last 5) ---")
            if not recent_sql:
                print("[No SQL executed yet]")
            else:
                for idx, s in enumerate(recent_sql, 1):
                    print(f"  {idx}. {s}")
        elif choice == "4":
            reset_database()
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()