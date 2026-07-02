import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=False, raise_error_if_not_found=False))

DATABASE_URL = os.environ.get("AI_DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "AI_DATABASE_URL is not set. Check your .env file in the workspace root."
    )

# pool_pre_ping=True reconnects automatically when Neon drops idle connections
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"connect_timeout": 30},
    pool_pre_ping=True,
    pool_recycle=300,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
