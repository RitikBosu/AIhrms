import os
from dotenv import load_dotenv
load_dotenv('d:/HRMS/.env')
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['HR_DATABASE_URL'])
with engine.connect() as conn:
    # Add columns to employees
    try:
        conn.execute(text('ALTER TABLE employees ADD COLUMN pto_balance_days FLOAT DEFAULT 20.0;'))
    except Exception as e:
        print("pto_balance_days probably exists:", e)
        
    try:
        conn.execute(text('ALTER TABLE employees ADD COLUMN sick_leave_balance_days FLOAT DEFAULT 10.0;'))
    except Exception as e:
        print("sick_leave_balance_days probably exists:", e)

    # Add columns to leaves
    try:
        conn.execute(text('ALTER TABLE leaves ADD COLUMN ai_justification VARCHAR;'))
    except Exception as e:
        print("ai_justification probably exists:", e)

    conn.commit()
print("Phase 7 Migration done")
