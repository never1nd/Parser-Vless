from database import SessionLocal, VlessKey, Source
from sqlalchemy import func

db = SessionLocal()
try:
    total_keys = db.query(func.count(VlessKey.id)).scalar()
    reality_keys = db.query(func.count(VlessKey.id)).filter(VlessKey.security == 'reality').scalar()
    working_keys = db.query(func.count(VlessKey.id)).filter(VlessKey.is_working == True).scalar()
    
    print(f"Total keys in DB: {total_keys}")
    print(f"Reality keys in DB: {reality_keys}")
    print(f"Working keys in DB: {working_keys}")
    
    if total_keys > 0:
        print("\nLast 5 keys sample:")
        last_keys = db.query(VlessKey).order_by(VlessKey.id.desc()).limit(5).all()
        for k in last_keys:
            print(f"- ID: {k.id}, Security: {k.security}, Working: {k.is_working}, URL: {k.raw_url[:50]}...")

    total_sources = db.query(func.count(Source.id)).scalar()
    active_sources = db.query(func.count(Source.id)).filter(Source.is_active == True).scalar()
    print(f"\nTotal sources: {total_sources}")
    print(f"Active sources: {active_sources}")

finally:
    db.close()
