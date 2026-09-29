from pathlib import Path
import runpy

import pytest


EXAMPLES = [
    "basic_schedule.py",
    "booking.py",
    "holds.py",
    "resource_pool.py",
]


@pytest.mark.parametrize("filename", EXAMPLES)
def test_example_scripts_run(filename):
    path = Path(__file__).parents[1] / "examples" / filename
    runpy.run_path(str(path), run_name="__main__")
