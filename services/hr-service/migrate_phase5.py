import os
from sqlalchemy import text
from app.database import engine

def run_migration():
    print("Starting Phase 5 database migration...")
    
    with engine.connect() as conn:
        print("Migrating 'employees' table...")
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN employment_type VARCHAR DEFAULT 'SALARIED';"))
            print(" - Added employment_type")
        except Exception as e:
            print(" - skipped employment_type (already exists or error:", str(e).split('\n')[0], ")")
            
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN max_weekly_hours INTEGER DEFAULT 40;"))
            print(" - Added max_weekly_hours")
        except Exception as e:
            print(" - skipped max_weekly_hours (already exists or error:", str(e).split('\n')[0], ")")

        print("Migrating 'attendance' table...")
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN clock_in TIMESTAMP WITH TIME ZONE;"))
            print(" - Added clock_in")
        except Exception as e:
            print(" - skipped clock_in (already exists or error:", str(e).split('\n')[0], ")")
            
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN clock_out TIMESTAMP WITH TIME ZONE;"))
            print(" - Added clock_out")
        except Exception as e:
            print(" - skipped clock_out (already exists or error:", str(e).split('\n')[0], ")")
            
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN ip_address VARCHAR;"))
            print(" - Added ip_address")
        except Exception as e:
            print(" - skipped ip_address (already exists or error:", str(e).split('\n')[0], ")")
            
        conn.commit()
    print("Migration finished.")
    
    # Also trigger create_all for new tables
    from app.database import create_db_and_tables
    create_db_and_tables()
    print("New tables (shifts, availability, shift_swap_requests) created if they didn't exist.")

if __name__ == "__main__":
    run_migration()
