from typing import Optional


def normalize_output(s: str) -> str:
    if s is None:
        return ""
    return "\n".join([line.rstrip() for line in s.strip().replace("\r\n", "\n").splitlines()])

def compare_outputs(actual: str, expected: str) -> bool:
    return normalize_output(actual) == normalize_output(expected)

def safe_truncate(s: str, max_len: int = 5000):
    if s is None:
        return ""
    if len(s) <= max_len:
        return s
    return s[:max_len] + "\n...[truncated]..."

def extract_stderr_info(stderr: str) -> Optional[str]:
    if not stderr:
        return None
    
    stderr = stderr.strip()
    if not stderr:
        return None
    
    lines = stderr.split("\n")
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    
    return None
