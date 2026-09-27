"""Compatibility entry point for the shared experimental preparation engine."""
from pathlib import Path
import sys

# Preserve direct script execution from outside the repository root.
_root=str(Path(__file__).resolve().parents[2])
if _root not in sys.path:sys.path.insert(0,_root)
from app.preparation.verify_record import *

if __name__=="__main__":main()
