import os
import json
import time
import requests
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# Fallback models list
MODELS = [
    MODEL_NAME,
    "nousresearch/hermes-3-llama-3.1-8b:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "qwen/qwen3-8b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

def get_action_from_llm(state: dict, task_id: str) -> dict:
    system_prompt = """You are a debugging agent. Fix broken Python code.

Available actions:
1. read_file   -> {"action_type": "read_file", "payload": {"filename": "app.py"}}
2. edit_code   -> {"action_type": "edit_code", "payload": {"filename": "app.py", "new_code": "COMPLETE FILE CONTENT"}}
3. run_tests   -> {"action_type": "run_tests", "payload": {}}
4. request_hint -> {"action_type": "request_hint", "payload": {}}

CRITICAL RULES:
- edit_code mein ALWAYS poora file content bhejo new_code key mein
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

            # Markdown backticks hataao
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

            # new_code fix — alag keys handle karo
            if action.get("action_type") == "edit_code":
                payload = action.get("payload", {})
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
                action["payload"]["new_code"] = new_code

            return action

        except Exception as e:
            err = str(e)
            if "429" in err:
                print(json.dumps({
                    "event": "RATE_LIMIT",
                    "model": model,
                    "waiting": "10s"
                }), flush=True)
                time.sleep(10)
            elif "404" in err:
                print(json.dumps({
                    "event": "MODEL_NOT_FOUND",
                    "model": model
                }), flush=True)
            else:
                print(json.dumps({
                    "event": "ERROR",
                    "model": model,
                    "error": err[:100]
                }), flush=True)
            continue

    return {"action_type": "run_tests", "payload": {}}


def run_task(task_id: str):
    print(json.dumps({"event": "[START]", "task_id": task_id}), flush=True)

    resp  = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id})
    state = resp.json()["state"]

    total_reward = 0.0
    step_num     = 0
    consecutive_run_tests = 0

    for _ in range(10):
        action = get_action_from_llm(state, task_id)

        # Stuck loop fix
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

        step_resp = requests.post(f"{ENV_URL}/step", json=action)
        result    = step_resp.json()

        state    = result["state"]
        reward   = result["reward"]
        done     = result["done"]
        message  = result.get("message", "")

        total_reward += reward
        step_num     += 1

        print(json.dumps({
            "event":   "[STEP]",
            "task_id": task_id,
            "step":    step_num,
            "action":  action,
            "reward":  reward,
            "done":    done,
            "message": message
        }), flush=True)

        if done:
            break

        time.sleep(1)  # rate limit se bachne ke liye

    print(json.dumps({
        "event":        "[END]",
        "task_id":      task_id,
        "total_reward": round(total_reward, 3),
        "steps":        step_num
    }), flush=True)

    return total_reward


if __name__ == "__main__":
    tasks  = ["easy", "medium", "hard"]
    scores = {}

    for task_id in tasks:
        score = run_task(task_id)
        scores[task_id] = score
        time.sleep(5)  # tasks ke beech wait

    print(json.dumps({
        "event":  "FINAL_SCORES",
        "scores": scores
    }), flush=True)