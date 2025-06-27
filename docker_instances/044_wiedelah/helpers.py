import os

def ensure_directory_exists(path: str, permissions: int = 0o755) -> bool:
    path = os.path.dirname(path)
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path, mode=permissions, exist_ok=True)
        return True
    except Exception:
        return False