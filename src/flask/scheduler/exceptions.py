"""
Scheduler exceptions
"""


class SchedulerError(Exception):
    """Base exception for scheduler errors"""
    pass


class TaskError(SchedulerError):
    """Task-related errors"""
    pass


class CronParseError(SchedulerError):
    """Cron expression parsing errors"""
    pass


class StorageError(SchedulerError):
    """Task storage errors"""
    pass