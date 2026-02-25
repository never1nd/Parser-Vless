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

def save_vless_keys_bulk(keys_list, security_type="none"):
    """
    Saves a list of VLESS keys to the database using bulk inserts.
    Uses 'insert or ignore' logic via manual SQL or handling duplicates in logic.
    """
    from sqlalchemy.dialects.sqlite import insert
    db = SessionLocal()
    try:
        if not keys_list:
            return
            
        # Deduplicate within the chunk and prepare values
        from utils.validator import is_reality
        
        for i in range(0, len(keys_list), 1000):
            chunk = keys_list[i : i + 1000]
            values = []
            for k in chunk:
                # Basic check to avoid empty or invalid entries
                if not k or "vless://" not in k: continue
                s_type = "reality" if is_reality(k) else "none" # Basic auto-detection
                values.append({"raw_url": k, "security": s_type})
            
            if values:
                stmt = insert(VlessKey).values(values).on_conflict_do_nothing()
                db.execute(stmt)
        db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in bulk save: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
