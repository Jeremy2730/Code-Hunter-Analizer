from collections import Counter

PENALTIES = {
    "CRITICAL": 20,
    "WARNING": 5,
    "INFO": 1
}

def calculate_health(findings):
    counts = Counter(
        f.level.value if hasattr(f.level, "value") else f.level
        for f in findings
    )

    score = 100
    for level, penalty in PENALTIES.items():
        score -= counts.get(level, 0) * penalty

    score = max(score, 0)

    status = (
        "CRITICAL" if score < 50
        else "WARNING" if score < 80
        else "HEALTHY"
    )

    return {
        "critical": counts.get("CRITICAL", 0),
        "warnings": counts.get("WARNING", 0),
        "info": counts.get("INFO", 0),
        "score": score,
        "status": status
    }
