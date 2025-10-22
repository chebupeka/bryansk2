import os
from dotenv import load_dotenv
load_dotenv()  # Загружает .env из корня проекта

import numpy as np
import hashlib
import secrets
from datetime import datetime
from scipy.stats import entropy
import logging  # Для debug

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, JSON, Float, String, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from nistrng import pack_sequence, check_eligibility_all_battery, run_all_battery, SP800_22R1A_BATTERY

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug env
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:gschn_demo@localhost:5432/gschn_demo')
print(f"Loaded env: DATABASE_URL={DATABASE_URL[:50]}...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine with pool_pre_ping for connection validation
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверяет соединение перед use
    pool_recycle=300,    # Recycle every 5 min
    echo=False  # True for SQL debug
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("DB tables created/checked OK")
except Exception as e:
    logger.error(f"DB init error (non-fatal): {e}")

# Migration: Add missing columns if table exists but old schema
db_mig = SessionLocal()
try:
    # Check if table exists
    result = db_mig.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'generations');"))
    if result.scalar():
        # Add columns if not exist
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS source VARCHAR;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS min_val INTEGER DEFAULT 0;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS max_val INTEGER DEFAULT 99;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS allow_duplicates BOOLEAN DEFAULT true;"))
        db_mig.commit()
        logger.info("Migration: Columns added OK")
    else:
        logger.info("No migration needed (table missing)")
except Exception as e:
    db_mig.rollback()
    logger.error(f"Migration error (non-fatal): {e}. Manual ALTER in pgAdmin if needed.")
finally:
    db_mig.close()

def chaotic_noise_generator(n=100, r=3.99, min_val=0, max_val=99, allow_duplicates=True):
    range_size = max_val - min_val + 1
    if range_size <= 0:
        raise ValueError("Range size must be positive")
    x = secrets.randbelow(1000000) / 1000000.0
    sequence = []
    for _ in range(n * 2 if not allow_duplicates else n):
        x = r * x * (1 - x)
        value = int(x * range_size) + min_val
        sequence.append(value)
    if not allow_duplicates:
        sequence = sorted(set(sequence))[:n]
    return sequence[:n]

def calculate_entropy(sequence):
    _, counts = np.unique(sequence, return_counts=True)
    probs = counts / len(sequence)
    ent = entropy(probs, base=2)
    return float(ent)

def chaotic_map_generator(n=100, r=3.99, x0=0.123, min_val=0, max_val=99, allow_duplicates=True):
    range_size = max_val - min_val + 1
    if range_size <= 0:
        raise ValueError("Range size must be positive")
    sequence = []
    x = x0
    for _ in range(n * 2 if not allow_duplicates else n):
        x = r * x * (1 - x)
        value = int((x * range_size) % range_size) + min_val
        sequence.append(value)
    if not allow_duplicates:
        sequence = sorted(set(sequence))[:n]
    return sequence[:n]

@app.get("/")
def home():
    return {"message": "TRNG + Хаос готов"}

@app.get("/generate/{source}")
def generate(source: str, n: int = 100, min_val: int = 0, max_val: int = 99, allow_duplicates: bool = True):
    try:
        if min_val > max_val:
            raise HTTPException(status_code=400, detail="min_val не может быть > max_val")
        if source == "chaotic":
            seq = chaotic_map_generator(n, min_val=min_val, max_val=max_val, allow_duplicates=allow_duplicates)
        elif source == "noise":
            seq = chaotic_noise_generator(n, min_val=min_val, max_val=max_val, allow_duplicates=allow_duplicates)
        else:
            raise HTTPException(status_code=400, detail="Источник: chaotic или noise")

        # Verify seq in range
        if not all(min_val <= v <= max_val for v in seq):
            raise HTTPException(status_code=500, detail="Generated values out of range")

        ent = calculate_entropy(seq)
        ts = datetime.now().isoformat()
        hash_val = hashlib.sha256(str(seq).encode()).hexdigest()

        db = SessionLocal()
        gen = Generation(
            sequence=seq,
            entropy_value=ent,
            timestamp=ts,
            hash_value=hash_val,
            source=source,
            min_val=min_val,
            max_val=max_val,
            allow_duplicates=allow_duplicates
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)
        db.close()

        logger.info(f"Generated {source}: ID={gen.id}, entropy={ent:.4f}")
        return {
            "id": gen.id,
            "sequence": seq,
            "entropy": ent,
            "timestamp": ts,
            "hash": hash_val,
            "generatedSource": gen.source,
            "generatedMin": gen.min_val,
            "generatedMax": gen.max_val,
            "generatedDuplicates": gen.allow_duplicates
        }
    except HTTPException:
        raise  # Re-raise FastAPI errors
    except Exception as e:
        logger.error(f"Generate error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/check_hash/{hash_val}")
def check_hash(hash_val: str):
    try:
        db = SessionLocal()
        gen = db.query(Generation).filter(Generation.hash_value == hash_val).first()
        db.close()
        if not gen:
            raise HTTPException(status_code=404, detail="Хэш не найден")
        return {
            "id": gen.id,
            "sequence": gen.sequence,
            "entropy": gen.entropy_value,
            "timestamp": gen.timestamp,
            "hash": gen.hash_value,
            "generatedSource": gen.source,
            "generatedMin": gen.min_val,
            "generatedMax": gen.max_val,
            "generatedDuplicates": gen.allow_duplicates
        }
    except Exception as e:
        logger.error(f"Check hash error: {e}")
        raise HTTPException(status_code=500, detail=f"Hash check failed: {str(e)}")

@app.get("/verify/{id}")
def verify(id: int):
    try:
        db = SessionLocal()
        gen = db.query(Generation).filter(Generation.id == id).first()
        db.close()
        if not gen:
            raise HTTPException(status_code=404, detail="Не найдено")
        return {
            "id": gen.id,
            "sequence": gen.sequence,
            "entropy": gen.entropy_value,
            "timestamp": gen.timestamp,
            "hash": gen.hash_value,
            "generatedSource": gen.source,
            "generatedMin": gen.min_val,
            "generatedMax": gen.max_val,
            "generatedDuplicates": gen.allow_duplicates
        }
    except Exception as e:
        logger.error(f"Verify error: {e}")
        raise HTTPException(status_code=500, detail=f"Verify failed: {str(e)}")

@app.get("/nist/{id}")
def nist_test(id: int):
    try:
        db = SessionLocal()
        gen = db.query(Generation).filter(Generation.id == id).first()
        db.close()
        if not gen:
            raise HTTPException(status_code=404, detail="Not found")

        binary_sequence = pack_sequence(gen.sequence)

        eligible_battery = check_eligibility_all_battery(binary_sequence, SP800_22R1A_BATTERY)
        if not eligible_battery:
            return {"id": id, "total_tests": 0, "passed": 0, "results": []}

        processed = []
        results = run_all_battery(binary_sequence, eligible_battery, False)

        for result, elapsed_time in results:
            processed.append({
                "test": result.name,
                "passed": result.passed,
                "score": np.round(result.score, 3) if result.passed else None
            })

        total = len(processed)
        passed_count = sum(1 for r in processed if r["passed"])

        return {
            "id": id,
            "total_tests": total,
            "passed": passed_count,
            "results": processed
        }
    except Exception as e:
        logger.error(f"NIST error: {e}")
        raise HTTPException(status_code=500, detail=f"NIST failed: {str(e)}")