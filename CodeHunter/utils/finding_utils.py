# CodeHunter/utils/finding_utils.py

from collections import defaultdict
from ..core.models import Category


def group_findings_by_category(findings):

    grouped = defaultdict(list)

    for finding in findings:
        grouped[finding.category].append(finding)

    return grouped


def summarize_findings(findings):

    grouped = group_findings_by_category(findings)

    return {
        "bugs": len(grouped[Category.BUG]),
        "vulnerabilities": len(grouped[Category.VULNERABILITY]),
        "smells": len(grouped[Category.CODE_SMELL]),
        "hotspots": len(grouped[Category.SECURITY_HOTSPOT]),
        "total": len(findings)
    }