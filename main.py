from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, JSON, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import numpy as np
from scipy.stats import entropy
import hashlib
from datetime import datetime

app = FastAPI()

# CORS для фронта
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Database setup
DATABASE_URL = "postgresql://postgres:12Hcrqa?@localhost:5433/gschn_demo"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, index=True)
    sequence = Column(JSON)  # Список чисел
    entropy_value = Column(Float)
    timestamp = Column(String)
    hash_value = Column(String)

Base.metadata.create_all(bind=engine)

def calculate_entropy(sequence):
    # Шенноновская энтропия для демонстрации (на дискретных значениях)
    _, counts = np.unique(sequence, return_counts=True)
    probs = counts / len(sequence)
    return float(entropy(probs, base=2))

def chaotic_map_generator(n=100, r=4.0, x0=0.5):
    # Логистическая карта для хаоса
    sequence = [x0]
    for _ in range(n-1):
        x = r * sequence[-1] * (1 - sequence[-1])
        sequence.append(x)
    return [int(x * 1000) % 100 for x in sequence]  # Нормализуем в 0-99

def noise_generator(n=100):
    # Симулированный шум (numpy random, но для реала используй pyaudio)
    return np.random.randint(0, 100, n).tolist()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/generate/{source}")
def generate(source: str, n: int = 100):
    if source == "chaotic":
        seq = chaotic_map_generator(n)
    elif source == "noise":
        seq = noise_generator(n)
    else:
        raise HTTPException(status_code=400, detail="Invalid source")

    ent = calculate_entropy(seq)
    ts = datetime.now().isoformat()
    hash_val = hashlib.sha256(str(seq).encode()).hexdigest()

    # Сохраняем в DB
    db = SessionLocal()
    gen = Generation(sequence=seq, entropy_value=ent, timestamp=ts, hash_value=hash_val)
    db.add(gen)
    db.commit()
    db.refresh(gen)

    return {"id": gen.id, "sequence": seq, "entropy": ent, "timestamp": ts, "hash": hash_val}

@app.get("/verify/{id}")
def verify(id: int):
    db = SessionLocal()
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Not found")
    return {"sequence": gen.sequence, "entropy": gen.entropy_value, "timestamp": gen.timestamp, "hash": gen.hash_value}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)