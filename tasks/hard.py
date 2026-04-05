HARD_TASK = {
    "task_id": "hard",
    "description": "app.py crashes at runtime. The bug is not in app.py itself — trace where get_value() comes from.",
    "total_tests": 4,

    "broken_files": {
        "utils.py": """\
def get_value():
    return "10"
""",
        "app.py": """\
from utils import get_value

def calculate(x):
    return x + get_value()

def double(x):
    return x * 2
"""
    },

    "correct_files": {
        "utils.py": """\
def get_value():
    return 10
""",
        "app.py": """\
from utils import get_value

def calculate(x):
    return x + get_value()

def double(x):
    return x * 2
"""
    },

    "hints": [
        "app.py imports something from utils.py. Read that file too.",
        "The error is a type mismatch — integer and string cannot be added."
    ]
}