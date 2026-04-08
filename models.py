from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class Task(BaseModel):
    id: str
    deadline: int = Field(..., ge=0)
    priority: int = Field(..., ge=1, le=3)
    estimated_time: int = Field(..., ge=1, le=3)
    urgency_score: int = Field(default=0, ge=0)
    completed: bool = False
    missed: bool = False


class Observation(BaseModel):
    step: int = Field(..., ge=0)
    time_elapsed: int = Field(..., ge=0)
    remaining_steps: int = Field(..., ge=0)
    tasks: List[Task]
    completed_task_ids: List[str]
    missed_task_ids: List[str]
    scenario: str
    hint: str


class ResetResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]


class StepRequest(BaseModel):
    task_id: str


class StepResponse(BaseModel):
    observation: Observation
    reward: float = Field(..., ge=0.0, le=1.0)
    done: bool
    info: Dict[str, Any]


class EnvState(BaseModel):
    observation: Observation
    done: bool
    mistakes: int = Field(..., ge=0)
    total_raw_reward: float
    total_normalized_reward: float = Field(..., ge=0.0, le=1.0)
    history: List[Dict[str, Any]]


class GradingResult(BaseModel):
    average_score: float = Field(..., ge=0.0, le=1.0)
    scenario_scores: Dict[str, float]
    details: Dict[str, Any]


class InferenceDecision(BaseModel):
    task_id: str
    reason: str

    @field_validator('task_id')
    @classmethod
    def strip_task_id(cls, value: str) -> str:
        return value.strip()

    @field_validator('reason')
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()
