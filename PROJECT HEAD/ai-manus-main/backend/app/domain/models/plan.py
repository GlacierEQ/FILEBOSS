from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Step(BaseModel):
    id: str
    description: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

    def is_done(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED or self.status == ExecutionStatus.FAILED

class Plan(BaseModel):
    id: str
    title: str
    goal: str
    steps: List[Step]
    message: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def is_done(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED or self.status == ExecutionStatus.FAILED
    
    def get_next_step(self) -> Optional[Step]:
        for step in self.steps:
            if not step.is_done():
                return step
        return None
