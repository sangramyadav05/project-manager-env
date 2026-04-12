from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
from openai import OpenAI
from pydantic import ValidationError

from models import InferenceDecision, Observation, Task

ENV_BASE_URL = os.getenv('ENV_BASE_URL', 'http://localhost:7860')
ENV_SCENARIO = os.getenv('ENV_SCENARIO', 'hard')
API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.openai.com/v1')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4.1-mini')
HF_TOKEN = os.getenv('HF_TOKEN')
LOCAL_IMAGE_NAME = os.getenv('LOCAL_IMAGE_NAME')


def choose_with_fallback(observation: Observation) -> InferenceDecision:
    ranked = sorted(observation.tasks, key=heuristic_sort_key, reverse=True)
    best = ranked[0]
    return InferenceDecision(
        task_id=best.id,
        reason='Fallback heuristic chose the best blend of priority, urgency score, and future step preservation.',
    )


def heuristic_sort_key(task: Task) -> tuple[float, float, float, float, str]:
    planning_bias = -(task.estimated_time - 1)
    return (task.priority, -task.urgency_score, planning_bias, -task.deadline, task.id)


def ask_openai(client: OpenAI, observation: Observation) -> InferenceDecision:
    payload = {
        'scenario': observation.scenario,
        'step': observation.step,
        'remaining_steps': observation.remaining_steps,
        'hint': observation.hint,
        'tasks': [task.model_dump() for task in observation.tasks],
        'completed_task_ids': observation.completed_task_ids,
        'missed_task_ids': observation.missed_task_ids,
        'instruction': 'Select exactly one task_id from the available tasks.',
    }
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                'role': 'system',
                'content': [
                    {
                        'type': 'text',
                        'text': (
                            'You are scheduling project tasks in a 3-step environment. '
                            'Analyze every available task internally. Compare business priority, deadline pressure, '
                            'urgency_score, estimated_time, and remaining_steps. Favor choices that reduce future '
                            'misses instead of acting greedily. Return strict JSON only with keys task_id and reason.'
                        ),
                    }
                ],
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(payload),
                    }
                ],
            },
        ],
        temperature=0,
    )
    return InferenceDecision.model_validate_json(response.output_text.strip())


def reset_env() -> Dict[str, Any]:
    response = requests.post(f'{ENV_BASE_URL}/reset', json={'scenario': ENV_SCENARIO}, timeout=30)
    response.raise_for_status()
    return response.json()


def step_env(task_id: str) -> Dict[str, Any]:
    response = requests.post(f'{ENV_BASE_URL}/step', json={'task_id': task_id}, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or os.getenv('OPENAI_API_KEY'))
    print('[START] resetting environment')
    reset_payload = reset_env()
    observation = Observation.model_validate(reset_payload['observation'])

    while True:
        try:
            decision = ask_openai(client, observation)
        except (ValidationError, json.JSONDecodeError, Exception):
            decision = choose_with_fallback(observation)

        print(
            '[STEP] '
            + json.dumps(
                {
                    'step': observation.step,
                    'selected_task_id': decision.task_id,
                    'reason': decision.reason,
                }
            )
        )

        step_payload = step_env(decision.task_id)
        print(
            '[STEP] '
            + json.dumps(
                {
                    'reward': step_payload['reward'],
                    'done': step_payload['done'],
                    'info': step_payload['info'],
                }
            )
        )

        if step_payload['done']:
            print('[END] ' + json.dumps({'final_observation': step_payload['observation'], 'final_info': step_payload['info']}))
            break

        observation = Observation.model_validate(step_payload['observation'])


if __name__ == '__main__':
    main()
