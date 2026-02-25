from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DB_PATH

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    type = Column(String)  # github, telegram, web
    channel = Column(String) # premium, free
    last_parsed = Column(DateTime)
    is_active = Column(Boolean, default=True)

class VlessKey(Base):
    __tablename__ = "keys"
    id = Column(Integer, primary_key=True)
    raw_url = Column(Text, unique=True, nullable=False)
    security = Column(String) # reality, tls, none
    is_working = Column(Boolean, default=False)
    latency = Column(Integer) # ms
    last_check = Column(DateTime, default=datetime.utcnow)
    discovery_date = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
