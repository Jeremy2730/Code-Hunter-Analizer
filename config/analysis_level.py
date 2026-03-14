from enum import Enum

class AnalysisLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


LEVEL_SEVERITY = {
    AnalysisLevel.BEGINNER: {"MAJOR", "CRITICAL"},
    AnalysisLevel.INTERMEDIATE: {"MINOR", "MAJOR", "CRITICAL"},
    AnalysisLevel.EXPERT: {"MINOR", "MAJOR", "CRITICAL"},
}

def filter_findings(findings, level):

    filtered = []

    for f in findings:

        if level == "Principiante":
            if f.severity in ["MAJOR", "CRITICAL"]:
                filtered.append(f)

        elif level == "Intermedio":
            if f.severity in ["MINOR", "MAJOR", "CRITICAL"]:
                filtered.append(f)

        elif level == "Experto":
            filtered.append(f)

    return filtered