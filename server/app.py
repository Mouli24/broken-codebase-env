from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import CodeEnv

app = FastAPI(
    title="Broken Codebase Repair Environment",
    description="OpenEnv environment where an AI agent debugs and fixes broken Python code.",
    version="1.0.0"
)

env = CodeEnv()

class Action(BaseModel):
    action_type: str
    payload: dict[str, Any] = {}

@app.get("/")
def root():
    return {"status": "ok", "message": "Broken Codebase Repair Environment is running."}

@app.post("/reset")
def reset(task_id: str = Query(default="easy", enum=["easy", "medium", "hard"])):
    state = env.reset(task_id)
    return {"state": state}

@app.post("/step")
def step(action: Action):
    state, reward, done, message = env.step(action.dict())
    return {"state": state, "reward": reward, "done": done, "message": message}

@app.get("/state")
def get_state():
    return {"state": env.get_state()}

@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "description": "Fix a syntax error in one file"},
            {"id": "medium", "description": "Fix a logic bug in one file"},
            {"id": "hard",   "description": "Fix a cross-file bug in two files"}
        ]
    }

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()