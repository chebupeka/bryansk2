from nistrng import pack_sequence, check_eligibility_all_battery, run_all_battery, SP800_22R1A_BATTERY
import numpy as np

def run_nist_tests(sequence):
    binary_sequence = pack_sequence(sequence)
    eligible_battery = check_eligibility_all_battery(binary_sequence, SP800_22R1A_BATTERY)
    if not eligible_battery:
        return {"id": None, "total_tests": 0, "passed": 0, "results": []}

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
        "id": None,  # For external, no ID
        "total_tests": total,
        "passed": passed_count,
        "results": processed
    }