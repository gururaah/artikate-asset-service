import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

class DatabaseHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseHandler, cls).__new__(cls)
            cls._instance.DATABASE_URL = "sqlite:///./artikate.db"
            
            cls._instance.engine = create_engine(
                cls._instance.DATABASE_URL, 
                connect_args={"check_same_thread": False} if "sqlite" in cls._instance.DATABASE_URL else {}
            )
            cls._instance.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=cls._instance.engine
            )
            cls._instance.Base = declarative_base()
        return cls._instance

# Global singleton instance
db_handler = DatabaseHandler()

engine = db_handler.engine
SessionLocal = db_handler.SessionLocal
Base = db_handler.Base

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()