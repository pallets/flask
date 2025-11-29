"""
Task storage for persisting task state and metrics
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .tasks import Task, TaskStatus
from .exceptions import StorageError


class TaskStorage:
    """Task state and metrics storage"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize storage"""
        self.storage_path = Path(storage_path) if storage_path else None
        self._lock = threading.RLock()
        self._tasks: Dict[str, Task] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def add_task(self, task: Task) -> None:
        """Add or update task"""
        with self._lock:
            self._tasks[task.name] = task
            if task.name not in self._metrics:
                self._metrics[task.name] = {}
            self._save_to_disk()
    
    def get_task(self, name: str) -> Optional[Task]:
        """Get task by name"""
        with self._lock:
            return self._tasks.get(name)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        with self._lock:
            return list(self._tasks.values())
    
    def remove_task(self, name: str) -> bool:
        """Remove task by name"""
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]
                if name in self._metrics:
                    del self._metrics[name]
                self._save_to_disk()
                return True
            return False
    
    def update_task_status(self, name: str, status: TaskStatus, 
                          error: Optional[str] = None) -> None:
        """Update task status"""
        with self._lock:
            task = self._tasks.get(name)
            if task:
                task.status = status
                if error:
                    task.last_error = error
                    task.metrics.last_error = error
                self._save_to_disk()
    
    def update_task_metrics(self, name: str, duration: float, 
                           success: bool, error: Optional[str] = None) -> None:
        """Update task execution metrics"""
        with self._lock:
            task = self._tasks.get(name)
            if task:
                metrics = task.metrics
                metrics.total_runs += 1
                metrics.last_run_at = datetime.now()
                
                if success:
                    metrics.successful_runs += 1
                    metrics.last_success_at = datetime.now()
                else:
                    metrics.failed_runs += 1
                    metrics.last_failure_at = datetime.now()
                    if error:
                        metrics.last_error = error
                
                # 更新平均执行时间
                if metrics.average_duration == 0:
                    metrics.average_duration = duration
                else:
                    metrics.average_duration = (metrics.average_duration + duration) / 2
                
                self._save_to_disk()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for all tasks"""
        with self._lock:
            total_tasks = len(self._tasks)
            enabled_tasks = sum(1 for task in self._tasks.values() if task.enabled)
            
            total_runs = 0
            successful_runs = 0
            failed_runs = 0
            
            for task in self._tasks.values():
                total_runs += task.metrics.total_runs
                successful_runs += task.metrics.successful_runs
                failed_runs += task.metrics.failed_runs
            
            return {
                'total_tasks': total_tasks,
                'enabled_tasks': enabled_tasks,
                'disabled_tasks': total_tasks - enabled_tasks,
                'total_executions': total_runs,
                'successful_executions': successful_runs,
                'failed_executions': failed_runs,
                'success_rate': (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                'tasks': {
                    task.name: task.to_dict() for task in self._tasks.values()
                }
            }
    
    def _save_to_disk(self) -> None:
        """Save state to disk"""
        if not self.storage_path:
            return
        
        try:
            data = {
                'tasks': {
                    name: task.to_dict() for name, task in self._tasks.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            # 使用临时文件确保原子性写入
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 原子性替换
            temp_path.replace(self.storage_path)
            
        except Exception as e:
            raise StorageError(f"Failed to save task state: {e}")
    
    def _load_from_disk(self) -> None:
        """Load state from disk"""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 这里简化处理，实际应该重建Task对象
            # 由于Task包含函数引用，序列化会比较复杂
            # 这里只恢复基本状态信息
            
        except Exception as e:
            # 加载失败不影响正常运行
            print(f"Warning: Failed to load task state: {e}")
    
    def cleanup_old_metrics(self, days: int = 30) -> int:
        """Clean up old metrics data"""
        # 这里可以实现更复杂的清理逻辑
        # 目前简化处理
        return 0