"""Prepare private storage without changing a caller-owned directory's permissions."""
from pathlib import Path


def prepare_database_path(value):
    path=Path(value)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    return path
