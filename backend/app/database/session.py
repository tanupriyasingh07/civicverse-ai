from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

def _build_engine():
    db_url = settings.DATABASE_URL
    try:
        eng = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with eng.connect() as conn:
            pass
        return eng
    except Exception:
        # Seamless local fallback when Docker Postgres is offline
        return create_engine("sqlite:///./civicverse_local.db", connect_args={"check_same_thread": False})

engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
