import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

Base = declarative_base()

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if DB_PASSWORD:
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


def drop_tables():
    Base.metadata.drop_all(engine)
    print("All tables have been dropped successfully.")


def drop_database():
    psycopg2_conn_params = {
        "dbname": "postgres",
        "user": DB_USER,
        "host": DB_HOST,
        "port": DB_PORT,
    }

    if DB_PASSWORD:
        psycopg2_conn_params["password"] = DB_PASSWORD

    conn = psycopg2.connect(**psycopg2_conn_params)
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{DB_NAME}' AND pid <> pg_backend_pid();"
    )

    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print(f"Database {DB_NAME} has been dropped successfully.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    drop_tables()
    drop_database()
