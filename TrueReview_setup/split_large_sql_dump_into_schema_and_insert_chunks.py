import os

INPUT_FILE = "truereview.sql"  # your dump file
SCHEMA_FILE = "truereview_schema.sql"
OUTPUT_PREFIX = "truereview_"
CHUNK_SIZE = 50000  # number of INSERTs per file

def is_create_table(line):
    return line.strip().upper().startswith("CREATE TABLE")

def is_insert(line):
    return line.strip().upper().startswith("INSERT INTO")

def split_sql_dump():
    schema_lines = []
    insert_lines = []
    
    print("Reading SQL dump...")

    with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if is_create_table(line):
                schema_lines.append(line)
                # Read until semicolon
                while ";" not in line:
                    line = next(f)
                    schema_lines.append(line)
            elif is_insert(line):
                insert_lines.append(line)

    print(f"Found {len(schema_lines)} schema lines")
    print(f"Found {len(insert_lines)} INSERT statements")

    # Write schema file
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        f.write("".join(schema_lines))

    print(f"Wrote schema to {SCHEMA_FILE}")

    # Split INSERTs into chunks
    chunk_index = 1
    counter = 0
    out_file = None

    for i, line in enumerate(insert_lines):
        if counter == 0:
            # open new chunk file
            filename = f"{OUTPUT_PREFIX}{chunk_index}.sql"
            out_file = open(filename, "w", encoding="utf-8")
            out_file.write("BEGIN;\n")
            print(f"Creating {filename}")

        out_file.write(line)
        counter += 1

        if counter >= CHUNK_SIZE:
            out_file.write("COMMIT;\n")
            out_file.close()
            chunk_index += 1
            counter = 0

    # Close last file
    if out_file and counter > 0:
        out_file.write("COMMIT;\n")
        out_file.close()

    print("Done!")
    print(f"Generated {chunk_index - 1} INSERT chunk files")

if __name__ == "__main__":
    split_sql_dump()
