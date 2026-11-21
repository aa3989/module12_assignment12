"""Initialize the application's PostgreSQL database tables."""

from app.database import Base, engine
import app.models


def init_db():
    """Create missing tables for registered models."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop registered tables (test/development use only)."""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    init_db()
