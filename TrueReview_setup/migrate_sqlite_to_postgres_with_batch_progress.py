import sqlite3
import psycopg2
import pandas as pd
from tqdm import tqdm
import os

# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------

SQLITE_DB_PATH = "/Users/parkernelson/Desktop/work/TrueReview/TrueReview.db"

PG_HOST = "dpg-d4qhtuh5pdvs738o9d90-a.oregon-postgres.render.com"
PG_DB = "truereview"
PG_USER = "truereview_admin"
PG_PASSWORD = "TrNMyIlmWQqxTBtiownOkjAPiNGT6bK6"
PG_PORT = 5432

BATCH_SIZE = 5000

# ---------------------------------------------------
# CONNECT
# ---------------------------------------------------

if not os.path.exists(SQLITE_DB_PATH):
    raise FileNotFoundError(f"SQLite DB not found at: {SQLITE_DB_PATH}")

sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)

pg_conn = psycopg2.connect(
    host=PG_HOST,
    database=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD,
    port=PG_PORT
)
pg_cursor = pg_conn.cursor()


def insert_table(table_name, pk_column=None):
    print(f"\n=== Copying {table_name} ===")

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)

    if df.empty:
        print(f"{table_name} is empty, skipping.")
        return

    columns = list(df.columns)
    col_names = ",".join(columns)
    placeholders = ",".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    rows = [tuple(r) for r in df.to_numpy()]
    total_rows = len(rows)

    # Progress bar around the batching loop
    for i in tqdm(range(0, total_rows, BATCH_SIZE), desc=f"Inserting {table_name}", unit="batch"):
        batch = rows[i:i+BATCH_SIZE]
        pg_cursor.executemany(insert_sql, batch)
        pg_conn.commit()

    print(f"Inserted {total_rows} rows into {table_name}")

    # Fix SERIAL sequences if required
    if pk_column:
        pg_cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name};")
        max_id = pg_cursor.fetchone()[0]

        if max_id is not None:
            pg_cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_column}'), {max_id}, TRUE);"
            )
            pg_conn.commit()
            print(f"Reset sequence for {table_name}.{pk_column} → {max_id}")


# ---------------------------------------------------
# MIGRATION ORDER
# ---------------------------------------------------

insert_table("users", pk_column="user_id")
insert_table("all_movies")
insert_table("movie_language_lkp")
insert_table("watched_list", pk_column="watched_id")

print("\n🎉 Migration with progress bars complete!")

sqlite_conn.close()
pg_conn.close()
