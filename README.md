---
title: Broken Codebase Repair Environment
emoji: 🔧
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

# Broken Codebase Repair Environment

An OpenEnv environment where an AI agent debugs and fixes broken Python code.

## Tasks
- **Easy**: Fix syntax error — missing colon in function definition
- **Medium**: Fix logic bug — wrong operator in divide function  
- **Hard**: Fix cross-file bug — type mismatch between utils.py and app.py

## Action Space
| Action | Payload |
|--------|---------|
| read_file | {"filename": "app.py"} |
| edit_code | {"filename": "app.py", "new_code": "..."} |
| run_tests | {} |
| request_hint | {} |

## Observation Space
| Field | Type |
|-------|------|
| files | dict |
| logs | list |
| tests_passed | int |
| total_tests | int |
| steps_taken | int |
| done | bool |

## Setup
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860

## Inference
export API_BASE_URL=https://openrouter.ai/api/v1
export MODEL_NAME=meta-llama/llama-3.2-3b-instruct:free
export HF_TOKEN=your-key
python inference.py

## Endpoints
- POST /reset?task_id=easy|medium|hard
- POST /step
- GET  /state
- GET  /tasks