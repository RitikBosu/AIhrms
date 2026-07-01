import os
import json
import threading

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "db.json")

global_db = None
db_lock = threading.Lock()
is_flushing = False
needs_flush = False

def read_db():
    global global_db
    if global_db is None:
        try:
            if os.path.exists(DB_PATH):
                with open(DB_PATH, 'r', encoding='utf-8') as f:
                    global_db = json.load(f)
            else:
                global_db = {"users": [], "employees": [], "attendance": [], "leaves": [], "candidates": [], "performance": [], "announcements": [], "jobDescription": ""}
        except Exception:
            global_db = {"users": [], "employees": [], "attendance": [], "leaves": [], "candidates": [], "performance": [], "announcements": [], "jobDescription": ""}
    return global_db

def flush_db_thread():
    global is_flushing, needs_flush
    with db_lock:
        if is_flushing or not needs_flush:
            return
        is_flushing = True
        needs_flush = False
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(global_db, f, indent=2)
    except Exception as e:
        print("Async DB write error:", e)
    finally:
        with db_lock:
            is_flushing = False
            if needs_flush:
                threading.Timer(0.05, flush_db_thread).start()

def write_db(db):
    global global_db, needs_flush
    global_db = db
    needs_flush = True
    if not is_flushing:
        flush_db_thread()
