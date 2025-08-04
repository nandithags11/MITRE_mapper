import openai
import psycopg2
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# openai key
openai.api_key =os.getenv("OPENAI_API_KEY")

# Pg conf

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}

TABLE_NAME ="nginx_logs"

# readfile to stripe first 5 lines
def read_lines(filepath):
    with open(filepath,"r") as f:
        return [next(f).stripe() for _ in range(5)]

#schema for file path
def gpt_schema(sample):
    prompt = f"""These are the first 5 lines of an NGINX log file:
{chr(10).join(sample)} lines of an NGINX log file:
{chr(10).join(sample)} lines of an NGINX log file:
{chr(10).join(sample)}

Please infer a SQL schema in PostgreSQL format with adding 2 more columns of MITRE_TTP as str and malicious as binary column. Output only the CREATE TABLE statement."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response['choices'][0]['message']['content']

#create table in db 
def create_table(conn,sql_schema):
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
    clean_stmt = sql_schema.replace("AUTOINCREMENT", "GENERATED ALWAYS AS IDENTITY")
    cur.execute(clean_stmt)
    conn.commit()

def insert_lines(conn,filepath):
    cur = conn.cursor()
    with open(filepath, "r") as f:
        for line in f:
            cur.execute(
                f"INSERT INTO {TABLE_NAME} (raw_line) VALUES (%s);", (line.strip(),)
            )
    conn.commit()


def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_log.py <nginx_log_file>")
        return
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print("File not found.")
        return

    sample = read_lines(filepath)
    print("Calling GPT for schema ...")

    sql_schema =gpt_schema(sample)
    print(sql_schema)

    conn = psycopg2.connect(**DB_CONFIG)
    create_table(conn,sql_schema)
    insert_lines(conn, filepath)
    print("Logs inserted into pg")



if __name__ =='__main__':
    main()