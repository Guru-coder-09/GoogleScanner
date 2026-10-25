"""Tests for CLI arguments and banner execution."""

import sys
import subprocess
from pathlib import Path

PYTHON_EXE = sys.executable
MAIN_PY = str(Path(__file__).parent.parent / "main.py")


def test_cli_help():
    res = subprocess.run(
        [PYTHON_EXE, MAIN_PY, "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "NeatWorkspace" in res.stdout
    assert "--drive" in res.stdout
    assert "--photos" in res.stdout
    assert "--undo" in res.stdout
    assert "--sim" in res.stdout
