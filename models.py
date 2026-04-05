from pydantic import BaseModel
from typing import Any

class Action(BaseModel):
    action_type: str   # "read_file" | "edit_code" | "run_tests" | "request_hint"
    payload: dict[str, Any] = {}

class StepResponse(BaseModel):
    state: dict
    reward: float
    done: bool
    message: str