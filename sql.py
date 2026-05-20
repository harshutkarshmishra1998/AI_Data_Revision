import os
import re
import sqlite3
import pandas as pd

# CONFIG
SQL_FILE = "query.sql"
DEFAULT_DB_DIR = "db"


def remove_sql_comments(sql_text):
    """Removes standard single-line and multi-line SQL comments."""
    sql_text = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
    sql_text = re.sub(r"--.*$", "", sql_text, flags=re.MULTILINE)
    return sql_text


with open(SQL_FILE, "r", encoding="utf-8") as file:
    raw_query = file.read()

fully_cleaned_text = remove_sql_comments(raw_query)

db_file_name = None
actual_query_blocks = []

for line in fully_cleaned_text.splitlines():
    line_stripped = line.strip()
    
    if not line_stripped:
        continue

    if line_stripped.upper().startswith("USE "):
        extracted_db = line_stripped[4:].strip().rstrip(";")
        if extracted_db:
            db_file_name = extracted_db
        continue

    actual_query_blocks.append(line)

clean_query = "\n".join(actual_query_blocks)

if not db_file_name:
    print("Error: No 'USE db_name' statement found in your SQL file.")
    exit()

DB_FILE = os.path.join(DEFAULT_DB_DIR, db_file_name)
OUTPUT_FILE = "query_results.xlsx"

print(f"Connecting to database: {DB_FILE}\n")

try:
    conn = sqlite3.connect(DB_FILE)

    individual_queries = [q.strip() for q in clean_query.split(";") if q.strip()]

    for i, statement in enumerate(individual_queries, 1):
        print(f"===== EXECUTING QUERY {i} =====")
        print(f"{statement}\n")
        
        df = pd.read_sql_query(statement, conn)
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        df.to_excel("query_results.xlsx", index=False)
        
        print("===== QUERY RESULT =====")
        print(df)
        print("\n" + "="*30 + "\n")

    conn.close()

except Exception as e:
    print(f"Error:\n{e}")