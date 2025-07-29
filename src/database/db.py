from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.conf.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

# SQLAlchemy Engine
# The engine is the starting point for any SQLAlchemy application. It's an object that
# manages a pool of connections to the database. `check_same_thread=False` is needed
# for SQLite when working with FastAPI to allow multiple threads to interact with the same connection.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# SQLAlchemy SessionLocal
# A SessionLocal instance is a database session. Each instance is a "holding zone"
# for all the objects you've loaded or associated with it during a single transaction.
# `autocommit=False` means that changes are not committed to the database automatically.
# `autoflush=False` means that objects are not flushed to the database until commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class for declarative models.

    All SQLAlchemy models in your application should inherit from this class.
    It provides the necessary metadata for SQLAlchemy to map Python classes to database tables.
    """
    pass

def get_db():
    """
    Dependency function to provide a database session.

    This function yields a database session that can be used by FastAPI
    dependency injection. It ensures the session is properly closed
    after the request is finished, regardless of success or failure.

    :yield: A SQLAlchemy database session.
    :rtype: :class:`sqlalchemy.orm.Session`
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()