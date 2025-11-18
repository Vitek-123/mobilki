from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

sql_url_db = "mysql+pymysql://root:root@localhost:3306/project_mobilki_aviasales"

engine = create_engine(
    sql_url_db,
    pool_pre_ping=True,
    pool_recycle=450,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()