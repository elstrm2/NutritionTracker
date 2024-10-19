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


def create_db_if_not_exists():
    if DB_PASSWORD:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
    else:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT,
        )

    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Database {DB_NAME} created successfully.")
    cursor.close()
    conn.close()


engine = create_engine(DATABASE_URL)


def create_database():
    create_db_if_not_exists()
    Base.metadata.create_all(engine)
    print("Tables have been created successfully.")


if __name__ == "__main__":
    create_database()
