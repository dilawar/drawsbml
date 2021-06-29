__author__ = "Dilawar Singh"
__email__ = "dilawar.s.rajput@gmail.com"

from pathlib import Path

import sys
import subprocess

sdir_ = Path(__file__).parent


def test_all():
    global sdir_
    files = sdir_.glob("*.*ml")
    for file in files:
        print(f"Converting {file}")
        s = subprocess.run(
            [sys.executable, "-m", "drawsbml", "-i", f"{file}"],
            check=True,
            capture_output=True,
        )
        print(s.stdout)


if __name__ == "__main__":
    test_all()
