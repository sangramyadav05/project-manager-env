# AI Project Manager Environment

## Problem Statement
This project provides a deterministic, multi-step OpenEnv-compatible environment where an AI agent acts as a project manager. The agent must pick tasks over a 3-step episode while balancing priority, deadlines, and scheduling stability.

## Task Explanation
Each task includes:
- `id`: unique task identifier
- `deadline`: integer countdown until the task becomes missed
- `priority`: importance from 1 to 3
- `estimated_time`: effort estimate from 1 to 3

At every step, the agent selects one `task_id` to complete. After the action:
- the chosen task is marked completed
- time advances by 1 unit
- all unfinished task deadlines decrease by 1
- tasks that hit `deadline == 0` before completion are marked missed and trigger penalties

The environment ships with three deterministic difficulty levels:
- `easy`: 2 tasks and a clear best choice
- `medium`: 3 tasks with deadline versus priority conflict
- `hard`: 4 tasks with meaningful trade-offs between urgency, impact, and estimated effort

## Reward Logic
Raw shaped reward is computed per step and then normalized to `[0, 1]` for OpenEnv compatibility.

Positive shaping:
- `+0.4` for selecting the highest-priority available task
- `+0.3` for selecting the earliest-deadline task
- `+0.2` for preserving the strongest long-term path across remaining steps
- `+0.1` for making a clean step without new mistakes

Penalties:
- `-0.5` for each task that misses its deadline on that step
- `-0.3` for poor prioritization
- `-0.1 * mistakes` as an accumulating memory penalty for repeated bad decisions

The environment also tracks cumulative raw reward and exposes a normalized total score in state and step metadata.

## Project Layout
- `models.py`: Pydantic request, response, and domain models
- `env.py`: deterministic environment logic and scenario definitions
- `grader.py`: baseline heuristic evaluator across all scenarios
- `server.py`: FastAPI server exposing `/reset`, `/step`, `/state`, and `/grade`
- `openenv.yaml`: OpenEnv metadata
- `inference.py`: OpenAI client-based inference loop with required logging tags
- `requirements.txt`: Python dependencies
- `Dockerfile`: container build for deployment

## Run Locally
### 1. Create a virtual environment and install dependencies
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### 2. Start the API and demo UI
```bash
uvicorn server:app --host 0.0.0.0 --port 7860
```

Open:
- `http://127.0.0.1:7860/` for the interactive browser demo
- `http://127.0.0.1:7860/docs` for FastAPI docs

### 3. Exercise the environment
Reset:
```bash
curl -X POST "http://localhost:7860/reset" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Step:
```bash
curl -X POST "http://localhost:7860/step" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "hard_security_review"}'
```

State:
```bash
curl "http://localhost:7860/state"
```

Grade the baseline heuristic:
```bash
python grader.py
```

## OpenAI Inference Client
`inference.py` is the only file that uses the OpenAI client. Set:
- `API_BASE_URL` (optional, defaults to `https://api.openai.com/v1`)
- `MODEL_NAME` (optional, defaults to `gpt-4.1-mini`)
- `HF_TOKEN` (preferred for hosted inference)
- `OPENAI_API_KEY` (supported fallback)
- `ENV_BASE_URL` (optional, defaults to `http://localhost:7860`)
- `ENV_SCENARIO` (optional, defaults to `hard`)
- `LOCAL_IMAGE_NAME` (optional, reserved for docker-based workflows)

Then run:
```bash
python inference.py
```

Logging format is intentionally strict:
- `[START]`
- `[STEP]`
- `[END]`

## Deploy with Docker
Build:
```bash
docker build -t ai-project-manager-environment .
```

Run:
```bash
docker run -p 7860:7860 ai-project-manager-environment
```

The container uses Python 3.10 and starts FastAPI on port `7860`.

## Notes for Judges
- Deterministic seeded behavior for repeatable scoring
- Multi-step episodes for richer decision making
- Shaped rewards instead of binary success/failure
- Observation `hint` field to help agent reasoning
- Step `info.reason`, `info.mistake`, and `info.strategy` fields for transparent reward attribution
- Built-in browser demo for fast live judging without needing curl or Postman
