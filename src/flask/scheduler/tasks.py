"""
Task models and enums
"""
import enum
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field


class TaskType(enum.Enum):
    """Task execution types"""
    INTERVAL = "interval"
    DELAY = "delay" 
    CRON = "cron"


class TaskStatus(enum.Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskMetrics:
    """Task execution metrics"""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    average_duration: float = 0.0
    last_error: Optional[str] = None


@dataclass
class Task:
    """Task definition and state"""
    name: str
    func: Callable
    task_type: TaskType
    
    # Timing configuration
    interval: Optional[timedelta] = None
    delay: Optional[timedelta] = None
    cron_expression: Optional[str] = None
    
    # Task metadata
    description: Optional[str] = None
    enabled: bool = True
    max_retries: int = 0
    timeout: Optional[timedelta] = None
    
    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    current_run_id: Optional[str] = None
    
    # Error tracking
    last_error: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        """Post-initialization setup"""
        if self.task_type == TaskType.INTERVAL and not self.interval:
            raise ValueError("Interval tasks must specify interval")
        if self.task_type == TaskType.DELAY and not self.delay:
            raise ValueError("Delay tasks must specify delay")
        if self.task_type == TaskType.CRON and not self.cron_expression:
            raise ValueError("Cron tasks must specify cron_expression")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            'name': self.name,
            'task_type': self.task_type.value,
            'description': self.description,
            'enabled': self.enabled,
            'max_retries': self.max_retries,
            'status': self.status.value,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'current_run_id': self.current_run_id,
            'last_error': self.last_error,
            'retry_count': self.retry_count,
            'metrics': {
                'total_runs': self.metrics.total_runs,
                'successful_runs': self.metrics.successful_runs,
                'failed_runs': self.metrics.failed_runs,
                'last_run_at': self.metrics.last_run_at.isoformat() if self.metrics.last_run_at else None,
                'last_success_at': self.metrics.last_success_at.isoformat() if self.metrics.last_success_at else None,
                'last_failure_at': self.metrics.last_failure_at.isoformat() if self.metrics.last_failure_at else None,
                'average_duration': self.metrics.average_duration,
                'last_error': self.metrics.last_error
            }
        }