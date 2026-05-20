import os
import re
import sqlite3
import pandas as pd

# CONFIG
SQL_FILE = "query_1.sql"
DEFAULT_DB_DIR = "db"  # Folder where your databases are kept


def remove_sql_comments(sql_text):
    """Removes standard single-line and multi-line SQL comments."""
    sql_text = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
    sql_text = re.sub(r"--.*$", "", sql_text, flags=re.MULTILINE)
    return sql_text


# READ SQL FILE
with open(SQL_FILE, "r", encoding="utf-8") as file:
    raw_query = file.read()

db_file_name = None
query_lines = []

# Process the query line by line
for line in raw_query.splitlines():
    cleaned_line = remove_sql_comments(line).strip()

    # Match "USE filename.db" or "USE superstore.db;"
    if cleaned_line.upper().startswith("USE "):
        # Extract everything after "USE ", removing semicolons and spaces
        extracted_db = cleaned_line[4:].strip().rstrip(";")
        if extracted_db:
            db_file_name = extracted_db
        # Skip adding this line to clean_query so SQLite won't execute it
        continue

    query_lines.append(line)

clean_query = "\n".join(query_lines)

# Verify if a database was specified in the file
if not db_file_name:
    print("Error: No 'USE db_name' statement found in your SQL file.")
    exit()

# CONSTRUCT THE DYNAMIC DB PATH
# This points to "db/superstore.db"
DB_FILE = os.path.join(DEFAULT_DB_DIR, db_file_name)

print(f"Connecting to database: {DB_FILE}\n")

# EXECUTE QUERY
try:
    conn = sqlite3.connect(DB_FILE)

    df = pd.read_sql_query(clean_query, conn)

    print("===== QUERY RESULT =====\n")
    print(df)

    conn.close()

except Exception as e:
    print(f"Error:\n{e}")
