# src/utils/database.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://marian:0303@localhost/computacion2"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from src.server.models import User, Image, Prediction 
    Base.metadata.create_all(bind=engine)  # Crea las tablas en la DB

