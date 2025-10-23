import io
import csv
from fastapi import UploadFile, File
from .generations import calculate_entropy, chaotic_noise_generator  # Reference gen
from .nist_service import run_nist_tests

def analyze_uploaded_sequence(file: UploadFile = File(...)):
    content = file.file.read().decode('utf-8')
    file.file.close()

    # Parse TXT/CSV or binary string
    seq = []
    try:
        # Check if it's a binary string (only 0s and 1s, possibly slitted)
        stripped_content = content.replace('\n', '').replace(' ', '').replace(',', '')
        if all(c in '01' for c in stripped_content):
            # Parse as individual bits
            for c in stripped_content:
                seq.append(int(c))
        else:
            # Try as line-separated TXT
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        num = int(line)
                        if 0 <= num <= 99:
                            seq.append(num)
                    except ValueError:
                        # Try as CSV if not int
                        try:
                            reader = csv.reader(io.StringIO(line))
                            for row in reader:
                                for val in row:
                                    val = val.strip()
                                    if val:
                                        num = int(val)
                                        if 0 <= num <= 99:
                                            seq.append(num)
                        except ValueError:
                            pass  # Skip invalid

        if len(seq) < 10:
            raise ValueError("Seq too short (<10 nums)")
    except Exception as e:
        raise ValueError(f"Parse error: {str(e)}")

    # User entropy/NIST
    user_entropy = calculate_entropy(seq)
    user_nist = run_nist_tests(seq)

    # Reference seq (secrets-based PRNG for comparison)
    ref_seq = chaotic_noise_generator(len(seq), min_val=0, max_val=99, allow_duplicates=True)
    ref_entropy = calculate_entropy(ref_seq)
    ref_nist = run_nist_tests(ref_seq)

    # Comparison table (simple dict)
    comparison = {
        "entropy": {"user": user_entropy, "ref": ref_entropy, "diff": abs(user_entropy - ref_entropy)},
        "nist_passed": {"user": user_nist["passed"], "ref": ref_nist["passed"], "total": user_nist["total_tests"]},
        "results": [  # Per test
            {
                "test": r["test"],
                "user_pass": r["passed"],
                "ref_pass": ref_r["passed"],
                "user_score": r["score"],
                "ref_score": ref_r["score"]
            } for r, ref_r in zip(user_nist["results"], ref_nist["results"])
        ]
    }

    return {
        "sequence": seq,
        "user_entropy": user_entropy,
        "user_nist": user_nist,
        "ref_entropy": ref_entropy,
        "ref_nist": ref_nist,
        "comparison": comparison
    }