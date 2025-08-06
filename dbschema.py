from openai import OpenAI
import psycopg2
import sys
import os
from dotenv import load_dotenv


# Load env variables
load_dotenv()

# openai key
client = OpenAI(api_key="OPENAI_API_KEY")

# Pg conf

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


# readfile to stripe first 5 lines
def read_lines(filepath):
    with open(filepath,"r") as f:
        return [next(f).strip() for _ in range(5)]

#schema for file path
def gpt_schema(sample):
    prompt = f"""These are the first 5 lines of an NGINX log file:
{chr(10).join(sample)} lines of an NGINX log file:
Please infer a SQL schema in PostgreSQL format with 2 extra columns:
- MITRE_TTP (text)
- malicious (boolean)

Output only the CREATE TABLE statement."""

    response = client.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response['choices'][0]['message']['content']

#create table in db 
def create_table(conn,sql_schema,TABLE_NAME):
    cur = conn.cursor()
    try:
        cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
        clean_stmt = sql_schema.replace("AUTOINCREMENT", "GENERATED ALWAYS AS IDENTITY")
        cur.execute(clean_stmt)
        conn.commit()
    except Exception as e:
        print(f"Error creating table {TABLE_NAME}: {e}")
        conn.rollback()
    finally:
        cur.close()

#insert lines into table
def insert_lines(conn,filepath):
    cur = conn.cursor()
    with open(filepath, "r") as f:
        for line in f:
            cur.execute(
                f"INSERT INTO {TABLE_NAME} (raw_line) VALUES (%s);", (line.strip(),)
            )
    conn.commit()


#update metadata table
def mark_file_as_updated(conn, meta_table):
    cur = conn.cursor()
    cur.execute("""
        UPDATE upload_metadata
        SET file_status = 'updated',
            updated_at = CURRENT_TIMESTAMP
        WHERE filename = %s;
    """, (meta_table,))
    conn.commit()
    cur.close()
    conn.close()

# main function to process log file
def process_log_file(filepath):
    if not os.path.exists(filepath):
        print("File not found.")
        return 
    
    #global variable for table name
    global TABLE_NAME
    filename_only = os.path.basename(filepath)
    TABLE_NAME = filename_only.replace('.', '_')

    conn = psycopg2.connect(**DB_CONFIG)

    
    sample = read_lines(filepath)
    print("Calling GPT for schema ...")

    sql_schema =gpt_schema(sample)
    print(sql_schema)

    create_table(conn,sql_schema,TABLE_NAME)

    # Insert lines into the table and update metadata table
    try:
        insert_lines(conn, filepath, TABLE_NAME)
        mark_file_as_updated(conn, filename_only)
        print(f"Processed and marked {filename_only} as updated.")
    except Exception as e:
        print(f"Error processing file: {e}")
        conn.rollback()

if __name__ =='__main__':
    if len(sys.argv) != 2:
        print("Usage: python dbschema.py <log_file>")
    else:
        process_log_file(sys.argv[1])
