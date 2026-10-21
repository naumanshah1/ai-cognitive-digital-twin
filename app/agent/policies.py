"""Security, authorization, and responsible AI safety policies for Milestone 8 agent."""

import re
from typing import Any, Dict, List, Optional, Tuple

# Strict allowlist of permissible agent tools
ALLOWED_TOOLS = {
    "get_behavioral_summary",
    "detect_behavioral_drift",
    "generate_recommendations",
    "run_what_if_simulation",
    "predict_productivity",
}

# Forbidden prompt injection patterns and shell/code execution attempts
PROHIBITED_CODE_PATTERNS = [
    r"__import__",
    r"eval\(",
    r"exec\(",
    r"os\.system",
    r"subprocess",
    r"shutil",
    r"open\(",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM",
    r"rm\s+-rf",
    r"<script>",
]

# Clinical and diagnostic terms strictly prohibited in non-clinical cognitive twin
PROHIBITED_CLINICAL_TERMS = [
    "burnout",
    "depression",
    "depressive",
    "clinical anxiety",
    "psychiatric",
    "mental illness",
    "pathology",
    "bipolar",
    "adhd diagnosis",
]

# Personal worth and derogatory judgements strictly prohibited
PROHIBITED_JUDGEMENTAL_TERMS = [
    "worthless",
    "incompetent",
    "stupid",
    "lazy",
    "inferior",
    "unfit",
    "defective",
]


class PolicyViolationError(ValueError):
    """Raised when an operation violates agent safety policies."""
    pass


def validate_tool_name(tool_name: str) -> bool:
    """Check if tool name is on the approved allowlist."""
    return tool_name in ALLOWED_TOOLS


def validate_user_scope(requested_user_id: Optional[str], target_user_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Enforce authorization boundaries to prevent cross-user data access."""
    if not target_user_id:
        return False, "Target user_id is missing."

    # Check format: synthetic_XXXX, synthetic_user_XX, or usr_XX
    if not re.match(r"^(synthetic_\d{4}|synthetic_user_\w+|synthetic_\d+|usr_\w+)$", target_user_id):
        return False, f"Invalid target user format: {target_user_id}."

    # If the request scoped an authorized user, ensure target matches
    if requested_user_id and target_user_id != requested_user_id:
        return False, f"Unauthorized cross-user access: requested {requested_user_id} but targeted {target_user_id}."

    return True, None


def check_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Detect injection attempts seeking arbitrary code execution or policy bypass."""
    for pattern in PROHIBITED_CODE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"Prohibited instruction or code pattern detected: {pattern}"
    return False, None


def validate_clinical_and_judgemental_safety(text: str) -> Tuple[bool, List[str]]:
    """Ensure generated content contains no clinical diagnoses or derogatory claims."""
    violations = []
    text_lower = text.lower()

    for term in PROHIBITED_CLINICAL_TERMS:
        if term in text_lower:
            violations.append(f"Prohibited clinical diagnosis term: '{term}'")

    for term in PROHIBITED_JUDGEMENTAL_TERMS:
        if term in text_lower:
            violations.append(f"Prohibited derogatory judgement term: '{term}'")

    is_safe = len(violations) == 0
    return is_safe, violations


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any], requested_user: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate argument bounds and authorization before tool execution."""
    if not validate_tool_name(tool_name):
        return False, f"Tool '{tool_name}' is not on the authorized allowlist."

    target_user = arguments.get("user_id") or requested_user
    is_valid_user, user_err = validate_user_scope(requested_user, target_user)
    if not is_valid_user:
        return False, user_err

    if tool_name == "get_behavioral_summary":
        days = arguments.get("days", 14)
        if not isinstance(days, (int, float)) or days < 1 or days > 365:
            return False, f"Argument 'days' must be between 1 and 365 (received {days})."

    elif tool_name == "detect_behavioral_drift":
        ref_w = arguments.get("ref_window", 14)
        cmp_w = arguments.get("cmp_window", 7)
        if not isinstance(ref_w, int) or ref_w < 7:
            return False, f"ref_window must be an integer >= 7 (received {ref_w})."
        if not isinstance(cmp_w, int) or cmp_w < 3:
            return False, f"cmp_window must be an integer >= 3 (received {cmp_w})."

    elif tool_name == "run_what_if_simulation":
        mods = arguments.get("modifications")
        if not isinstance(mods, dict) or len(mods) == 0:
            return False, "modifications must be a non-empty dictionary of feature perturbations."
        task_type = arguments.get("task_type", "retrospective")
        if task_type not in ["retrospective", "forecasting"]:
            return False, f"task_type must be 'retrospective' or 'forecasting' (received '{task_type}')."

    elif tool_name == "predict_productivity":
        task_type = arguments.get("task_type", "retrospective")
        if task_type not in ["retrospective", "forecasting"]:
            return False, f"task_type must be 'retrospective' or 'forecasting' (received '{task_type}')."

    return True, None


def enforce_resource_limits(
    current_iteration: int,
    tool_calls_count: int,
    max_steps: int = 8,
    max_tool_calls: int = 5,
) -> Tuple[bool, Optional[str]]:
    """Enforce non-overridable step and tool call budgets."""
    if current_iteration >= max_steps:
        return False, f"Execution halted: Maximum step budget reached ({current_iteration}/{max_steps})."
    if tool_calls_count >= max_tool_calls:
        return False, f"Execution halted: Maximum tool call budget reached ({tool_calls_count}/{max_tool_calls})."
    return True, None
