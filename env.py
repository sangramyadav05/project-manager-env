from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Tuple

from models import EnvState, Observation, Task

EPISODE_LENGTH = 3
RANDOM_SEED = 7
STEP_RAW_MIN = -1.6
STEP_RAW_MAX = 1.0
TOTAL_RAW_MIN = STEP_RAW_MIN * EPISODE_LENGTH
TOTAL_RAW_MAX = STEP_RAW_MAX * EPISODE_LENGTH

SCENARIOS: Dict[str, List[Task]] = {
    'easy': [
        Task(id='easy_high', deadline=2, priority=3, estimated_time=1),
        Task(id='easy_low', deadline=4, priority=1, estimated_time=1),
    ],
    'medium': [
        Task(id='med_urgent', deadline=1, priority=2, estimated_time=1),
        Task(id='med_critical', deadline=3, priority=3, estimated_time=2),
        Task(id='med_backlog', deadline=4, priority=1, estimated_time=1),
    ],
    'hard': [
        Task(id='hard_client_escalation', deadline=1, priority=2, estimated_time=1),
        Task(id='hard_platform_cutover', deadline=2, priority=3, estimated_time=3),
        Task(id='hard_security_review', deadline=2, priority=3, estimated_time=2),
        Task(id='hard_ops_handoff', deadline=3, priority=2, estimated_time=1),
    ],
}

SCENARIO_HINTS: Dict[str, str] = {
    'easy': 'A single high-priority task is clearly dominant. Finish it before cleanup work.',
    'medium': 'Priority and deadline pull in different directions. Avoid early deadline misses.',
    'hard': 'Two top-priority items compete with a client escalation and only three steps remain. Greedy play is risky.',
}


class ProjectManagerEnv:
    def __init__(self, scenario: str = 'easy') -> None:
        self._random = random.Random(RANDOM_SEED)
        self.scenario = scenario
        self.tasks: List[Task] = []
        self.step_count = 0
        self.time_elapsed = 0
        self.done = False
        self.mistakes = 0
        self.total_raw_reward = 0.0
        self.history: List[Dict[str, Any]] = []
        self._reset_internal(scenario)

    async def reset(self, scenario: str | None = None) -> Dict[str, Any]:
        try:
            observation, info = self._reset_internal(scenario)
            return {
                'observation': observation.model_dump(),
                'reward': 0.0,
                'done': False,
                'info': info,
            }
        except Exception as exc:
            fallback_observation = self._build_observation().model_dump()
            return {
                'observation': fallback_observation,
                'reward': 0.0,
                'done': False,
                'info': {'error': str(exc)},
            }

    async def step(self, action: Dict[str, Any] | str) -> Dict[str, Any]:
        try:
            if isinstance(action, dict):
                task_id = str(action.get('task_id', '')).strip()
            else:
                task_id = str(action).strip()

            if self.done:
                raise ValueError('Episode is already complete. Call reset() to start a new episode.')
            if not task_id:
                raise ValueError('Missing task_id in action.')

            available = [task for task in self.tasks if not task.completed and not task.missed]
            selected = next((task for task in available if task.id == task_id), None)
            if selected is None:
                raise ValueError(f'Invalid task_id: {task_id}')

            highest_priority = max(task.priority for task in available)
            earliest_deadline = min(task.deadline for task in available)
            planning_candidates = self._planning_candidates(available)

            raw_reward = 0.0
            step_has_mistake = False
            reason_parts: List[str] = []
            mistake_parts: List[str] = []
            strategy_parts: List[str] = []

            if selected.priority == highest_priority:
                raw_reward += 0.4
                reason_parts.append('The choice matches the highest available priority.')
            else:
                raw_reward -= 0.3
                step_has_mistake = True
                mistake_parts.append('A higher-priority task was available but not selected.')

            if selected.deadline == earliest_deadline:
                raw_reward += 0.3
                reason_parts.append('The choice addresses the earliest active deadline.')
            else:
                strategy_parts.append('The agent accepted some deadline risk to protect broader value.')

            if selected.id in planning_candidates:
                raw_reward += 0.2
                reason_parts.append('The choice preserves the strongest long-term path across remaining steps.')
            else:
                step_has_mistake = True
                mistake_parts.append('The action weakens the remaining schedule compared with safer alternatives.')

            selected.completed = True
            strategy_parts.append(f'Completed {selected.id} and advanced the schedule by one time unit.')

            self.step_count += 1
            self.time_elapsed += 1

            missed_now = self._advance_time_and_mark_missed()
            if missed_now:
                raw_reward -= 0.5 * len(missed_now)
                step_has_mistake = True
                mistake_parts.append('Missed deadline(s): ' + ', '.join(task.id for task in missed_now) + '.')

            if step_has_mistake:
                self.mistakes += 1
                raw_reward -= 0.1 * self.mistakes
                strategy_parts.append(f'Memory penalty applied because mistakes have accumulated to {self.mistakes}.')
            else:
                raw_reward += 0.1
                strategy_parts.append('No mistakes recorded on this step.')

            self.total_raw_reward += raw_reward
            self.done = self.step_count >= EPISODE_LENGTH or all(task.completed or task.missed for task in self.tasks)

            normalized_step_reward = self._clamp_reward(self._normalize_step_reward(raw_reward))
            total_normalized = self._clamp_reward(self._normalize_total_reward(self.total_raw_reward))

            info = {
                'reason': ' '.join(reason_parts) or 'The action completed a task.',
                'mistake': ' '.join(mistake_parts) or 'No tactical mistakes were identified on this step.',
                'strategy': ' '.join(strategy_parts),
                'raw_reward': round(raw_reward, 4),
                'total_raw_reward': round(self.total_raw_reward, 4),
                'total_normalized_reward': round(total_normalized, 4),
                'mistakes': self.mistakes,
                'missed_tasks_this_step': [task.id for task in missed_now],
                'completed_task_id': selected.id,
            }
            self.history.append(
                {
                    'step': self.step_count,
                    'selected_task_id': selected.id,
                    'raw_reward': round(raw_reward, 4),
                    'normalized_reward': round(normalized_step_reward, 4),
                    'done': self.done,
                    'info': info,
                }
            )

            return {
                'observation': self._build_observation().model_dump(),
                'reward': round(normalized_step_reward, 4),
                'done': self.done,
                'info': info,
            }
        except Exception as exc:
            return {
                'observation': self._build_observation().model_dump(),
                'reward': 0.0,
                'done': self.done,
                'info': {'error': str(exc)},
            }

    async def state(self) -> EnvState:
        return EnvState(
            observation=self._build_observation(),
            done=self.done,
            mistakes=self.mistakes,
            total_raw_reward=round(self.total_raw_reward, 4),
            total_normalized_reward=round(self._clamp_reward(self._normalize_total_reward(self.total_raw_reward)), 4),
            history=self.history,
        )

    async def close(self) -> Dict[str, Any]:
        self.done = True
        return {
            'scenario': self.scenario,
            'message': 'Environment closed.',
            'total_normalized_reward': round(self._clamp_reward(self._normalize_total_reward(self.total_raw_reward)), 4),
        }

    def _reset_internal(self, scenario: str | None = None) -> Tuple[Observation, Dict[str, Any]]:
        if scenario is not None:
            if scenario not in SCENARIOS:
                raise ValueError(f'Unknown scenario: {scenario}')
            self.scenario = scenario

        self.tasks = copy.deepcopy(SCENARIOS[self.scenario])
        self.step_count = 0
        self.time_elapsed = 0
        self.done = False
        self.mistakes = 0
        self.total_raw_reward = 0.0
        self.history = []

        observation = self._build_observation()
        info = {
            'scenario': self.scenario,
            'seed': RANDOM_SEED,
            'reason': f'Reset environment for the {self.scenario} scenario.',
            'mistake': 'No mistakes have been made yet.',
            'strategy': 'Balance priority, urgency, and remaining step budget.',
        }
        return observation, info

    def _advance_time_and_mark_missed(self) -> List[Task]:
        missed_now: List[Task] = []
        for task in self.tasks:
            if task.completed or task.missed:
                continue
            task.deadline = max(task.deadline - 1, 0)
            if task.deadline == 0:
                task.missed = True
                missed_now.append(task)
        return missed_now

    def _build_observation(self) -> Observation:
        visible_tasks: List[Task] = []
        for task in self.tasks:
            if task.completed or task.missed:
                continue
            visible_task = task.model_copy(deep=True)
            visible_task.urgency_score = max(visible_task.deadline - self.time_elapsed, 0)
            visible_tasks.append(visible_task)

        completed_task_ids = [task.id for task in self.tasks if task.completed]
        missed_task_ids = [task.id for task in self.tasks if task.missed]
        return Observation(
            step=self.step_count,
            time_elapsed=self.time_elapsed,
            remaining_steps=max(EPISODE_LENGTH - self.step_count, 0),
            tasks=visible_tasks,
            completed_task_ids=completed_task_ids,
            missed_task_ids=missed_task_ids,
            scenario=self.scenario,
            hint=self._build_hint(visible_tasks),
        )

    def _build_hint(self, available_tasks: List[Task]) -> str:
        base_hint = SCENARIO_HINTS[self.scenario]
        if not available_tasks:
            return base_hint + ' No active tasks remain.'

        highest_priority = max(task.priority for task in available_tasks)
        earliest_deadline = min(task.deadline for task in available_tasks)
        highest_urgency = min(task.urgency_score for task in available_tasks)
        return (
            f'{base_hint} Highest priority available: {highest_priority}. '
            f'Earliest active deadline: {earliest_deadline}. '
            f'Most urgent task score: {highest_urgency}.'
        )

    def _planning_candidates(self, available: List[Task]) -> List[str]:
        ranked = sorted(
            available,
            key=lambda task: (
                self._projected_risk(task),
                -task.priority,
                task.deadline,
                task.estimated_time,
                task.id,
            ),
        )
        best_risk = self._projected_risk(ranked[0])
        return [task.id for task in ranked if self._projected_risk(task) == best_risk]

    def _projected_risk(self, selected: Task) -> Tuple[int, int, int]:
        projected_misses = 0
        projected_pressure = 0
        remaining_steps = max(EPISODE_LENGTH - self.step_count - 1, 0)
        for task in self.tasks:
            if task.completed or task.missed or task.id == selected.id:
                continue
            projected_deadline = max(task.deadline - 1, 0)
            if projected_deadline == 0:
                projected_misses += 1
            elif projected_deadline <= remaining_steps:
                projected_pressure += 1
        return (projected_misses, projected_pressure, selected.estimated_time)

    @staticmethod
    def _normalize_step_reward(raw_reward: float) -> float:
        clipped = min(max(raw_reward, STEP_RAW_MIN), STEP_RAW_MAX)
        return (clipped - STEP_RAW_MIN) / (STEP_RAW_MAX - STEP_RAW_MIN)

    @staticmethod
    def _normalize_total_reward(raw_reward: float) -> float:
        clipped = min(max(raw_reward, TOTAL_RAW_MIN), TOTAL_RAW_MAX)
        return (clipped - TOTAL_RAW_MIN) / (TOTAL_RAW_MAX - TOTAL_RAW_MIN)

    @staticmethod
    def _clamp_reward(reward: float) -> float:
        return max(0.0, min(1.0, reward))
