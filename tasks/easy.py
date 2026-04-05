EASY_TASK = {
    "task_id": "easy",
    "description": "Fix the syntax error in app.py. The function definition is missing something.",
    "total_tests": 2,

    # Ye agent ko milega — broken code
    "broken_files": {
        "app.py": """\
def add(a, b)
    return a + b

def subtract(a, b):
    return a - b
"""
    },

    # Ye grader use karega check karne ke liye
    "correct_files": {
        "app.py": """\
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    },

    # Agent hint maang sakta hai (optional feature)
    "hints": [
        "Look at the first line of the add function carefully.",
        "Function definitions in Python need a specific character at the end."
    ]
}