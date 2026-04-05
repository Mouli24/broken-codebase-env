from tasks import ALL_TASKS

def grade(task_id: str, current_files: dict) -> float:
    score = 0.0

    if task_id == "easy":
        code = current_files.get("app.py", "")
        if "def add(a, b):" in code:
            score += 0.5
        if "return a + b" in code:
            score += 0.5

    elif task_id == "medium":
        code = current_files.get("app.py", "")
        if "return a / b" in code:
            score += 1.0

    elif task_id == "hard":
        utils_code = current_files.get("utils.py", "")
        app_code = current_files.get("app.py", "")

        if "return 10" in utils_code and '"10"' not in utils_code:
            score += 0.5

        if "int(get_value())" in app_code or ("return 10" in utils_code and "return x + get_value()" in app_code):
            score += 0.2

        if "from utils import get_value" in app_code:
            score += 0.2

        if "return x * 2" in app_code:
            score += 0.1

    return round(min(score, 1.0), 2)


def run_tests(task_id: str, current_files: dict) -> dict:
    score = grade(task_id, current_files)
    total = ALL_TASKS[task_id]["total_tests"]
    passed = round(score * total)

    return {
        "passed": passed,
        "total": total,
        "score": score
    }