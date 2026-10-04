from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import settings

database_url = settings.DATABASE_URL
connect_args = {}
engine_kwargs = {}

if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if ":memory:" in database_url:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    database_url,
    connect_args=connect_args,
    **engine_kwargs,
    future=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
