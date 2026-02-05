"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from contextlib import contextmanager

# Database URL - supports PostgreSQL, SQLite, MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./nba_analytics.db"  # Default to SQLite for development
)

# Fix for PostgreSQL URLs from some hosting providers (they use postgres:// instead of postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True to see SQL queries
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI endpoints to get database session
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions (non-FastAPI use)
    
    Usage:
        with get_db_context() as db:
            # use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models.py
    """
    from database_models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def reset_db():
    """
    DANGER: Drops all tables and recreates them
    Only use in development!
    """
    from database_models import Base
    print("⚠️  WARNING: Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables recreated")


def get_db_info():
    """Get information about the database connection"""
    return {
        "database_type": DATABASE_URL.split("://")[0],
        "database_url": DATABASE_URL.replace(os.getenv("DB_PASSWORD", ""), "****") if "DB_PASSWORD" in os.environ else DATABASE_URL,
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
        "echo": engine.echo
    }


# Test database connection
def test_connection():
    """Test if database connection works"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run this file directly to initialize database
    print("🗄️  Initializing database...")
    print(f"Database URL: {DATABASE_URL}")
    
    # Test connection
    if test_connection():
        # Create tables
        init_db()
        
        # Show info
        info = get_db_info()
        print("\n📊 Database Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Failed to connect to database. Check your DATABASE_URL.")