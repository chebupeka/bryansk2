import numpy as np
import hashlib
import secrets
from datetime import datetime
from scipy.stats import entropy
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, JSON, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from nistrng import pack_sequence, check_eligibility_all_battery, run_all_battery, SP800_22R1A_BATTERY

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATABASE_URL = "postgresql://postgres:gschn_demo?@localhost:5432/gschn_demo"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, index=True)
    sequence = Column(JSON)
    entropy_value = Column(Float)
    timestamp = Column(String)
    hash_value = Column(String)

Base.metadata.create_all(bind=engine)

def chaotic_noise_generator(n=100, r=3.99):
    x = secrets.randbelow(1000000) / 1000000.0
    sequence = []
    for _ in range(n):
        x = r * x * (1 - x)
        value = int(x * 100) % 100
        sequence.append(value)
    return sequence

def calculate_entropy(sequence):
    _, counts = np.unique(sequence, return_counts=True)
    probs = counts / len(sequence)
    ent = entropy(probs, base=2)
    return float(ent)

def chaotic_map_generator(n=100, r=3.99, x0=0.123):
    sequence = []
    x = x0
    for _ in range(n):
        x = r * x * (1 - x)
        value = int((x * 100) % 100)
        sequence.append(value)
    return sequence

@app.get("/")
def home():
    return {"message": "TRNG + Хаос готов"}

@app.get("/generate/{source}")
def generate(source: str, n: int = 100):
    if source == "chaotic":
        seq = chaotic_map_generator(n)
    elif source == "noise":
        seq = chaotic_noise_generator(n)
    else:
        raise HTTPException(status_code=400, detail="Источник: chaotic или noise")

    ent = calculate_entropy(seq)
    ts = datetime.now().isoformat()
    hash_val = hashlib.sha256(str(seq).encode()).hexdigest()

    db = SessionLocal()
    try:
        gen = Generation(
            sequence=seq,
            entropy_value=ent,
            timestamp=ts,
            hash_value=hash_val,
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return {
        "id": gen.id,
        "sequence": seq,
        "entropy": ent,
        "timestamp": ts,
        "hash": hash_val
    }

@app.get("/verify/{id}")
def verify(id: int):
    db = SessionLocal()
    try:
        gen = db.query(Generation).filter(Generation.id == id).first()
        if not gen:
            raise HTTPException(status_code=404, detail="Не найдено")
        return {
            "id": gen.id,
            "sequence": gen.sequence,
            "entropy": gen.entropy_value,
            "timestamp": gen.timestamp,
            "hash": gen.hash_value
        }
    finally:
        db.close()

@app.get("/nist/{id}")
def nist_test(id: int):
    db = SessionLocal()
    try:
        gen = db.query(Generation).filter(Generation.id == id).first()
        if not gen:
            raise HTTPException(status_code=404, detail="Not found")

        binary_sequence = pack_sequence(gen.sequence)

        eligible_battery: dict = check_eligibility_all_battery(binary_sequence, SP800_22R1A_BATTERY)
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
        raise HTTPException(status_code=500, detail=f"NIST error: {str(e)}")
    finally:
        db.close()