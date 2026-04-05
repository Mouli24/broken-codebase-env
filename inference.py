import os
import json
import time
import requests
from openai import OpenAI

# Checklist Item 2 & 3 — Environment variables
API_BASE_URL     = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME       = os.getenv("MODEL_NAME", "qwen/qwen3.6-plus:free")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
ENV_URL          = os.getenv("ENV_URL", "https://Mouli24-broken-codebase-env.hf.space")

# Checklist Item 4 — OpenAI client
client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

BENCHMARK = "broken-codebase-repair"
TASKS     = ["easy", "medium", "hard"]
MODELS    = [
    MODEL_NAME,
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen3-8b:free",
]

# Checklist Item 5 — Exact log format
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def get_action_from_llm(state: dict, task_id: str) -> dict:
    system_prompt = """You are a debugging agent. Fix broken Python code.

Available actions:
1. read_file    -> {"action_type": "read_file", "payload": {"filename": "app.py"}}
2. edit_code    -> {"action_type": "edit_code", "payload": {"filename": "app.py", "new_code": "COMPLETE FILE"}}
3. run_tests    -> {"action_type": "run_tests", "payload": {}}
4. request_hint -> {"action_type": "request_hint", "payload": {}}

RULES:
- edit_code mein ALWAYS poora file content new_code key mein bhejo
- Sirf JSON respond karo — koi explanation nahi
- new_code key ka naam bilkul new_code hi rakho

Available files: """ + str(list(state.get("files", {}).keys()))

    user_prompt = f"""
Task: {task_id}
Steps: {state.get('steps_taken')}/{state.get('max_steps')}
Tests passed: {state.get('tests_passed')}/{state.get('total_tests')}
Logs: {state.get('logs', [])[-3:]}
Files:
{json.dumps(state.get('files', {}), indent=2)}
Next action? JSON only:"""

    for model in MODELS:
        if not model:
            continue
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ]
            )
            raw = response.choices[0].message.content
            if raw is None:
                continue
            raw = raw.strip()

            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:]
                    part = part.strip()
                    if part.startswith("{"):
                        raw = part
                        break

            action = json.loads(raw.strip())

            if action.get("action_type") == "edit_code":
                payload  = action.get("payload", {})
                new_code = (
                    payload.get("new_code") or
                    payload.get("code") or
                    payload.get("content") or
                    payload.get("file_content") or
                    payload.get("new_content") or
                    payload.get("updated_code") or
                    payload.get("fixed_code") or ""
                )
                action["payload"]["new_code"] = new_code

            return action

        except Exception as e:
            err = str(e)
            if "429" in err:
                time.sleep(10)
            continue

    return {"action_type": "run_tests", "payload": {}}


def run_task(task_id: str):
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards     = []
    steps_taken = 0
    success     = False

    try:
        resp  = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id})
        state = resp.json()["state"]
    except Exception as e:
        log_end(success=False, steps=0, score=0.0, rewards=[])
        return 0.0

    consecutive_run_tests = 0

    for _ in range(10):
        action = get_action_from_llm(state, task_id)

        if action.get("action_type") == "run_tests":
            consecutive_run_tests += 1
            if consecutive_run_tests >= 2:
                unread = [f for f in state["files"].keys()
                         if f"Read file: {f}" not in str(state["logs"])]
                if unread:
                    action = {"action_type": "read_file",
                             "payload": {"filename": unread[0]}}
                    consecutive_run_tests = 0
        else:
            consecutive_run_tests = 0

        try:
            step_resp = requests.post(f"{ENV_URL}/step", json=action)
            result    = step_resp.json()
        except Exception as e:
            log_step(steps_taken + 1, action.get("action_type", "unknown"), 0.0, False, str(e))
            break

        state   = result["state"]
        reward  = result["reward"]
        done    = result["done"]

        rewards.append(reward)
        steps_taken += 1

        log_step(
            step=steps_taken,
            action=action.get("action_type", "unknown"),
            reward=reward,
            done=done,
            error=None
        )

        if done:
            if state.get("tests_passed") == state.get("total_tests"):
                success = True
            break

        time.sleep(1)

    score = max(rewards) if rewards else 0.0
    score = min(max(score, 0.0), 1.0)

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score


if __name__ == "__main__":
    all_scores = {}

    for task_id in TASKS:
        score          = run_task(task_id)
        all_scores[task_id] = score
        time.sleep(5)

    print(f"[FINAL] scores={json.dumps(all_scores)}", flush=True)