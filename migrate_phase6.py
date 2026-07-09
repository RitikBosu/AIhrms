import os
from dotenv import load_dotenv
load_dotenv('d:/HRMS/.env')
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['HR_DATABASE_URL'])
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE shifts ALTER COLUMN employee_id DROP NOT NULL;'))
    conn.execute(text("CREATE TABLE IF NOT EXISTS shift_bids (id SERIAL PRIMARY KEY, shift_id INTEGER NOT NULL REFERENCES shifts(id), employee_id INTEGER NOT NULL REFERENCES employees(id), status VARCHAR NOT NULL DEFAULT 'Pending', created_at VARCHAR);"))
    conn.commit()
print("Migration done")
