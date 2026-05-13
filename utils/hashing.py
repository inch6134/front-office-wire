import hashlib


def make_job_id(value: str) -> str:
    """SHA-256 hash of a URL or native job ID, truncated to 16 hex chars."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]
