"""Rebuild the v2 pipeline end to end: python v2/run_all.py"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
STEPS = ["s01_bbs_extract.py", "s02_gee_extract.py", "s03_build_panel.py",
         "s04_analysis.py", "s05_figures.py", "make_reference_docx.py", "s06_manuscript.py"]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, "-W", "ignore", step], cwd=SRC, check=True)
