from sqlalchemy import Column, Integer, JSON, Float, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, index=True)
    sequence = Column(JSON)
    entropy_value = Column(Float)
    timestamp = Column(String)
    hash_value = Column(String)
    source = Column(String)  # 'chaotic' or 'noise'
    min_val = Column(Integer)
    max_val = Column(Integer)
    allow_duplicates = Column(Boolean)