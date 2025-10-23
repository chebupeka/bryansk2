import hashlib
from datetime import datetime
import logging

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from nistrng import pack_sequence, check_eligibility_all_battery, SP800_22R1A_BATTERY, run_all_battery
from sqlalchemy import text

from components.database import engine, SessionLocal
from components.generations import chaotic_map_generator, chaotic_noise_generator, calculate_entropy
from components.models import Base, Generation
from components.nist_service import run_nist_tests
from components.analyze import analyze_uploaded_sequence


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"Loaded DATABASE_URL={engine.url[:50]}...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Migration
db_mig = SessionLocal()
try:
    Base.metadata.create_all(bind=engine)
    result = db_mig.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'generations');"))
    if result.scalar():
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS source VARCHAR;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS min_val INTEGER DEFAULT 0;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS max_val INTEGER DEFAULT 99;"))
        db_mig.execute(text("ALTER TABLE generations ADD COLUMN IF NOT EXISTS allow_duplicates BOOLEAN DEFAULT true;"))
        db_mig.commit()
        logger.info("Migration OK")
except Exception as e:
    db_mig.rollback()
    logger.error(f"Migration error: {e}")
finally:
    db_mig.close()

@app.get("/")
def home():
    return {"message": "TRNG + Хаос готов"}

@app.get("/generate/{source}")
def generate(source: str, n: int = 100, min_val: int = 0, max_val: int = 99, allow_duplicates: bool = True):
    try:
        if source == "chaotic":
            seq = chaotic_map_generator(n, min_val=min_val, max_val=max_val, allow_duplicates=allow_duplicates)
        elif source == "noise":
            seq = chaotic_noise_generator(n, min_val=min_val, max_val=max_val, allow_duplicates=allow_duplicates)
        else:
            raise HTTPException(status_code=400, detail="Источник: chaotic или noise")

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

        logger.info(f"Generated {source}: ID={gen.id}")
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
        raise
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

# New: Upload analysis endpoint
@app.post("/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    try:
        result = analyze_uploaded_sequence(file)
        logger.info(f"Analyzed upload: len={len(result['sequence'])}, entropy={result['user_entropy']:.4f}")
        return result
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")