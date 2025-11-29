"""
Task decorators for easy task definition
"""
import functools
from datetime import timedelta
from typing import Callable, Optional
from .tasks import Task, TaskType

# 延迟导入避免循环依赖
_scheduler = None

def get_scheduler():
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        try:
            from .scheduler import Scheduler
            _scheduler = Scheduler.get_instance()
        except ImportError:
            pass
    return _scheduler


def interval_task(interval: timedelta, name: Optional[str] = None, 
                 description: Optional[str] = None, enabled: bool = True,
                 max_retries: int = 0, timeout: Optional[timedelta] = None):
    """
    Decorator for interval-based tasks
    
    Args:
        interval: Task execution interval
        name: Task name (default: function name)
        description: Task description
        enabled: Whether task is enabled
        max_retries: Maximum retry attempts
        timeout: Task timeout
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        # 创建任务定义
        task = Task(
            name=task_name,
            func=func,
            task_type=TaskType.INTERVAL,
            interval=interval,
            description=description or func.__doc__,
            enabled=enabled,
            max_retries=max_retries,
            timeout=timeout
        )
        
        # 注册到调度器
        scheduler = get_scheduler()
        if scheduler:
            scheduler.add_task(task)
        
        # 保持原始函数可用
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 附加任务信息
        wrapper._scheduler_task = task
        wrapper._scheduler_task_name = task_name
        
        return wrapper
    
    return decorator


def delay_task(delay: timedelta, name: Optional[str] = None,
              description: Optional[str] = None, enabled: bool = True,
              max_retries: int = 0, timeout: Optional[timedelta] = None):
    """
    Decorator for delayed tasks
    
    Args:
        delay: Delay before execution
        name: Task name (default: function name)
        description: Task description
        enabled: Whether task is enabled
        max_retries: Maximum retry attempts
        timeout: Task timeout
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        # 创建任务定义
        task = Task(
            name=task_name,
            func=func,
            task_type=TaskType.DELAY,
            delay=delay,
            description=description or func.__doc__,
            enabled=enabled,
            max_retries=max_retries,
            timeout=timeout
        )
        
        # 注册到调度器
        scheduler = get_scheduler()
        if scheduler:
            scheduler.add_task(task)
        
        # 保持原始函数可用
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 附加任务信息
        wrapper._scheduler_task = task
        wrapper._scheduler_task_name = task_name
        
        return wrapper
    
    return decorator


def cron_task(cron_expression: str, name: Optional[str] = None,
             description: Optional[str] = None, enabled: bool = True,
             max_retries: int = 0, timeout: Optional[timedelta] = None):
    """
    Decorator for cron-based tasks
    
    Args:
        cron_expression: Cron expression (5 fields: minute hour day month weekday)
        name: Task name (default: function name)
        description: Task description
        enabled: Whether task is enabled
        max_retries: Maximum retry attempts
        timeout: Task timeout
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        # 创建任务定义
        task = Task(
            name=task_name,
            func=func,
            task_type=TaskType.CRON,
            cron_expression=cron_expression,
            description=description or func.__doc__,
            enabled=enabled,
            max_retries=max_retries,
            timeout=timeout
        )
        
        # 注册到调度器
        scheduler = get_scheduler()
        if scheduler:
            scheduler.add_task(task)
        
        # 保持原始函数可用
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 附加任务信息
        wrapper._scheduler_task = task
        wrapper._scheduler_task_name = task_name
        
        return wrapper
    
    return decorator