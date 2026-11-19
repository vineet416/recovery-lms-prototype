from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# Parent class that every database model inherits from.
class Base(DeclarativeBase):
    pass


# Gives one database session to a request and always closes it afterwards.
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Creates every table that does not exist yet.
def create_tables() -> None:
    import app.models  # noqa: F401  (importing registers all tables on Base)

    Base.metadata.create_all(engine)
