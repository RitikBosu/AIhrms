import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv, find_dotenv

# Walk up directories to find .env (works from any working directory)
load_dotenv(find_dotenv(usecwd=False, raise_error_if_not_found=False))

DATABASE_URL = os.environ.get("HR_DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "HR_DATABASE_URL is not set. Check your .env file in the workspace root."
    )

# connect_timeout prevents silent hangs on cold Neon connections
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"connect_timeout": 30},
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
