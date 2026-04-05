MEDIUM_TASK = {
    "task_id": "medium",
    "description": "The divide function has a logic bug. It runs without error but gives wrong output.",
    "total_tests": 3,

    "broken_files": {
        "app.py": """\
def divide(a, b):
    return a * b

def multiply(a, b):
    return a * b

def add(a, b):
    return a + b
"""
    },

    "correct_files": {
        "app.py": """\
def divide(a, b):
    return a / b

def multiply(a, b):
    return a * b

def add(a, b):
    return a + b
"""
    },

    "hints": [
        "The divide function runs without crashing. Think about what it returns.",
        "Check which operator is being used inside divide."
    ]
}