import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# static files and templates

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#pg connection
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

#created upload metadat table
cur.execute("""
CREATE TABLE IF NOT EXISTS upload_metadata (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    table_name TEXT NOT NULL
);
""")

@app.get("/", response_class=HTMLResponse)
def upload_file(request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.log'):
        raise HTTPException(status_code=400, detail="Only .log files are allowed")
    
    # Save the uploaded file
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    # Insert metadata into the database
    table_name = file.filename.replace('.', '_')
    cur.execute("INSERT INTO upload_metadata (filename, table_name) VALUES (%s, %s)", (file.filename, table_name))
    conn.commit()
    
    return {"info": f"File '{file.filename}' uploaded successfully", "table_name": table_name}