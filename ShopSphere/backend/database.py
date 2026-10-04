import os
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
import mysql.connector
def load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///shopsphere.db"
)

def create_db_engine():
    global DATABASE_URL
    if "mysql" in DATABASE_URL:
        try:
            parsed = urllib.parse.urlparse(DATABASE_URL)
            db_name = parsed.path.lstrip("/") or "shopsphere_db"
            user = parsed.username or "root"
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306

            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connection_timeout=2
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            cursor.close()
            conn.close()
            print(f"[Database] Ensured MySQL database '{db_name}' exists.")
            return create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
        except Exception as e:
            print(f"[Database Warning] MySQL unavailable ({e}). Falling back to SQLite.")
            DATABASE_URL = "sqlite:///shopsphere.db"
            return create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                echo=False
            )
    else:
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False
        )

engine = create_db_engine()

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

def get_db():
    """Contextual session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
