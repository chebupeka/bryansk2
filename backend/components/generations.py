import secrets
import numpy as np
from scipy.stats import entropy

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

def calculate_entropy(sequence):
    _, counts = np.unique(sequence, return_counts=True)
    probs = counts / len(sequence)
    ent = entropy(probs, base=2)
    return float(ent)