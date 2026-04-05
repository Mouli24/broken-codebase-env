from tasks import ALL_TASKS
from grader import grade, run_tests

class CodeEnv:
    def __init__(self):
        self.task_id = None
        self.files = {}
        self.logs = []
        self.tests_passed = 0
        self.total_tests = 0
        self.steps_taken = 0
        self.max_steps = 10
        self.done = False
        self.hints_used = 0

    def reset(self, task_id: str = "easy") -> dict:
        task = ALL_TASKS[task_id]

        self.task_id = task_id
        self.files = dict(task["broken_files"])
        self.logs = []
        self.tests_passed = 0
        self.total_tests = task["total_tests"]
        self.steps_taken = 0
        self.done = False
        self.hints_used = 0

        return self._build_state()

    def step(self, action: dict) -> tuple:
        if self.done:
            return self._build_state(), 0.0, True, "Episode already done. Call reset()."

        action_type = action.get("action_type")
        payload = action.get("payload", {})
        reward = 0.0
        message = ""

        # ── ACTION 1: read_file ──────────────────────────
        if action_type == "read_file":
            filename = payload.get("filename", "")

            if filename in self.files:
                self.logs.append(f"Read file: {filename}")
                reward = 0.1
                message = f"Successfully read {filename}"
            else:
                self.logs.append(f"File not found: {filename}")
                reward = -0.05
                message = f"File '{filename}' does not exist. Available: {list(self.files.keys())}"

        # ── ACTION 2: edit_code ──────────────────────────
        elif action_type == "edit_code":
            filename = payload.get("filename", "")

            # LLM alag alag key names use karta hai - sab handle karo
            new_code = (
                payload.get("new_code") or
                payload.get("code") or
                payload.get("content") or
                payload.get("file_content") or
                payload.get("new_content") or
                payload.get("updated_code") or
                payload.get("fixed_code") or
                ""
            )

            if filename not in self.files:
                reward = -0.1
                message = f"Cannot edit '{filename}' — file does not exist."
            elif new_code.strip() == "":
                reward = -0.1
                message = "new_code cannot be empty."
            else:
                old_code = self.files[filename]
                self.files[filename] = new_code
                self.logs.append(f"Edited file: {filename}")

                # Grader se check karo kitna sahi fix hai
                new_score = grade(self.task_id, self.files)
                old_score = grade(self.task_id,
                                  {**self.files, filename: old_code})

                improvement = new_score - old_score

                if improvement > 0:
                    reward = improvement
                    message = f"Good edit! Score improved by {improvement}"
                elif improvement == 0:
                    reward = 0.0
                    message = "Edit made but no improvement in score."
                else:
                    reward = -0.2
                    message = "Edit made things worse! A working part may have broken."

        # ── ACTION 3: run_tests ──────────────────────────
        elif action_type == "run_tests":
            result = run_tests(self.task_id, self.files)
            self.tests_passed = result["passed"]
            reward = result["score"]
            message = f"Tests: {result['passed']}/{result['total']} passed. Score: {result['score']}"

            if result["passed"] == result["total"]:
                self.done = True
                message += " — All tests passed! Task complete."

        # ── ACTION 4: request_hint ───────────────────────
        elif action_type == "request_hint":
            task = ALL_TASKS[self.task_id]
            hints = task.get("hints", [])

            if self.hints_used < len(hints):
                hint = hints[self.hints_used]
                self.hints_used += 1
                self.logs.append(f"Hint used: {hint}")
                reward = -0.05
                message = f"Hint: {hint}"
            else:
                message = "No more hints available."
                reward = 0.0

        # ── UNKNOWN ACTION ───────────────────────────────
        else:
            reward = -0.1
            message = f"Unknown action '{action_type}'. Valid: read_file, edit_code, run_tests, request_hint"

        # Step count badhao
        self.steps_taken += 1
        if self.steps_taken >= self.max_steps:
            self.done = True
            message += f" | Max steps ({self.max_steps}) reached."

        state = self._build_state()
        return state, round(reward, 3), self.done, message

    def get_state(self) -> dict:
        return self._build_state()

    def _build_state(self) -> dict:
        return {
            "task_id": self.task_id,
            "files": self.files,
            "logs": self.logs,
            "tests_passed": self.tests_passed,
            "total_tests": self.total_tests,
            "steps_taken": self.steps_taken,
            "max_steps": self.max_steps,
            "done": self.done,
            "hints_used": self.hints_used
        }