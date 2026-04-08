from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from env import ProjectManagerEnv, SCENARIOS
from models import GradingResult, Observation, Task


class HeuristicProjectManager:
    def choose_task(self, observation: Observation) -> str:
        ranked = sorted(observation.tasks, key=self._task_score, reverse=True)
        return ranked[0].id

    @staticmethod
    def _task_score(task: Task) -> Tuple[float, float, float, float, str]:
        planning_bias = -(task.estimated_time - 1)
        return (task.priority, -task.urgency_score, planning_bias, -task.deadline, task.id)


async def run_episode(env: ProjectManagerEnv, agent: HeuristicProjectManager) -> Dict[str, Any]:
    state = await env.state()
    trace: List[Dict[str, Any]] = []

    while not state.done:
        task_id = agent.choose_task(state.observation)
        observation, reward, done, info = await env.step(task_id)
        trace.append(
            {
                'task_id': task_id,
                'reward': reward,
                'done': done,
                'info': info,
                'remaining_tasks': [task.model_dump() for task in observation.tasks],
            }
        )
        state = await env.state()

    return {
        'score': state.total_normalized_reward,
        'trace': trace,
        'history': state.history,
    }


async def grade_all() -> GradingResult:
    agent = HeuristicProjectManager()
    scenario_scores: Dict[str, float] = {}
    details: Dict[str, Any] = {}

    for scenario in SCENARIOS:
        env = ProjectManagerEnv(scenario=scenario)
        outcome = await run_episode(env, agent)
        scenario_scores[scenario] = round(outcome['score'], 4)
        details[scenario] = outcome
        await env.close()

    average_score = round(sum(scenario_scores.values()) / len(scenario_scores), 4)
    return GradingResult(
        average_score=average_score,
        scenario_scores=scenario_scores,
        details=details,
    )


if __name__ == '__main__':
    result = asyncio.run(grade_all())
    print(result.model_dump_json(indent=2))
