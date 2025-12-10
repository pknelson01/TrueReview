import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from tqdm import tqdm
import time
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

MAIN_BATCH_SIZE = 5000
MICRO_BATCH_SIZE = 250
RECONNECT_RETRIES = 5

# ---------------------------------------------------
# CONNECT TO POSTGRES (WITH RETRIES)
# ---------------------------------------------------

def pg_connect():
    for attempt in range(RECONNECT_RETRIES):
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                database=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD,
                port=PG_PORT
            )
            cur = conn.cursor()
            return conn, cur
        except Exception as e:
            print(f"Connection attempt {attempt+1} failed, retrying...")
            time.sleep(2)
    raise Exception("Failed to connect to PostgreSQL after several retries.")

# Global connection objects
pg_conn, pg_cursor = pg_connect()

# ---------------------------------------------------
# START SQLITE CONNECTION
# ---------------------------------------------------
sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)


# ---------------------------------------------------
# INSERT FUNCTION WITH RECONNECT SUPPORT
# ---------------------------------------------------

def insert_table(table_name, pk_column=None):
    global pg_conn, pg_cursor  # IMPORTANT FIX

    print(f"\n=== Copying {table_name} ===")

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)

    if df.empty:
        print(f"{table_name} is empty — skipping.")
        return

    columns = list(df.columns)
    col_names = ",".join(columns)
    placeholders = ",".join(["%s"] * len(columns))

    insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    all_rows = [tuple(r) for r in df.to_numpy()]
    total_rows = len(all_rows)

    # Loop with main progress bar
    for i in tqdm(range(0, total_rows, MAIN_BATCH_SIZE), desc=f"Inserting {table_name}", unit="batch"):
        batch = all_rows[i:i+MAIN_BATCH_SIZE]

        # Micro-batch loop
        for j in range(0, len(batch), MICRO_BATCH_SIZE):
            micro = batch[j:j+MICRO_BATCH_SIZE]

            try:
                execute_batch(pg_cursor, insert_sql, micro, page_size=MICRO_BATCH_SIZE)
            except Exception as e:
                print(f"\n⚠️ Insert error: {e}")
                print("Reconnecting to PostgreSQL…")

                # Try reconnecting
                try:
                    pg_conn.close()
                except:
                    pass

                time.sleep(1)
                pg_conn, pg_cursor = pg_connect()

                # Retry the failed micro-batch
                execute_batch(pg_cursor, insert_sql, micro, page_size=MICRO_BATCH_SIZE)

        pg_conn.commit()

    print(f"Inserted {total_rows:,} rows into {table_name}")

    # Fix sequence if SERIAL table
    if pk_column:
        pg_cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name};")
        max_id = pg_cursor.fetchone()[0]

        if max_id:
            pg_cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_column}'), {max_id}, TRUE);"
            )
            pg_conn.commit()
            print(f"Sequence reset for {table_name}.{pk_column} → {max_id}")


# ---------------------------------------------------
# RUN MIGRATION
# ---------------------------------------------------

insert_table("users", pk_column="user_id")
insert_table("all_movies")
insert_table("movie_language_lkp")
insert_table("watched_list", pk_column="watched_id")

print("\n🎉 Migration completed successfully — stable version with reconnects!")

sqlite_conn.close()
pg_conn.close()
