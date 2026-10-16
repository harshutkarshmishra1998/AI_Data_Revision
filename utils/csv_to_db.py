import pandas as pd
import sqlite3
from pathlib import Path


def csv_to_sqlite(csv_path, db_path=None, table_name=None):

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Default DB name = same as CSV
    if db_path is None:
        db_path = csv_path.with_suffix(".db")

    # Default table name = csv filename
    if table_name is None:
        table_name = csv_path.stem.replace(" ", "_")

    # Read CSV
    df = pd.read_csv(csv_path)

    # Create SQLite DB
    conn = sqlite3.connect(db_path)

    # Write dataframe to SQL table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()

    print(f"Database created: {db_path}")
    print(f"Table name: {table_name}")


# Example usage
if __name__ == "__main__":
    csv_file = "subscription_info.csv"

    csv_to_sqlite(csv_file)