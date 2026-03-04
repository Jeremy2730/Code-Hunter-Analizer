from .bug_detector import detect_bugs
from .vulnerability_scanner import detect_vulnerabilities
from .code_smell_detector import detect_code_smells
from .security_hotspots import detect_security_hotspots


from .advanced_diagnostics import (
    run_advanced_analysis,
    get_findings_by_severity,
    get_findings_by_category,
    get_top_issues,
    get_files_with_most_issues
)