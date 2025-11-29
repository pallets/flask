"""
Flask Scheduler - Main scheduler implementation
"""
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future

from flask import Flask, current_app
from .tasks import Task, TaskType, TaskStatus
from .storage import TaskStorage
from .cron import CronParser
from .exceptions import SchedulerError, TaskError
from .blueprint import create_scheduler_blueprint


logger = logging.getLogger(__name__)


class Scheduler:
    """Flask任务调度器"""
    
    _instance = None
    _instance_lock = threading.Lock()
    
    def __init__(self, app: Optional[Flask] = None, storage_path: Optional[str] = None):
        """初始化调度器"""
        self.app = app
        self.storage = TaskStorage(storage_path)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running_tasks: Dict[str, Future] = {}
        self._tick_interval = 1.0  # 默认1秒检查间隔
        self._max_workers = 4
        self._enabled = True
        self._autostart = True
        
        if app is not None:
            self.init_app(app)
    
    @classmethod
    def get_instance(cls) -> Optional['Scheduler']:
        """获取调度器实例"""
        return cls._instance
    
    def init_app(self, app: Flask) -> None:
        """初始化Flask应用"""
        self.app = app
        
        # 配置项
        app.config.setdefault('SCHEDULER_ENABLED', True)
        app.config.setdefault('SCHEDULER_AUTOSTART', True)
        app.config.setdefault('SCHEDULER_TICK_INTERVAL', 1.0)
        app.config.setdefault('SCHEDULER_MAX_WORKERS', 4)
        app.config.setdefault('SCHEDULER_STORAGE_PATH', None)
        
        # 应用配置
        self._enabled = app.config['SCHEDULER_ENABLED']
        self._autostart = app.config['SCHEDULER_AUTOSTART']
        self._tick_interval = app.config['SCHEDULER_TICK_INTERVAL']
        self._max_workers = app.config['SCHEDULER_MAX_WORKERS']
        
        # 重新初始化存储
        storage_path = app.config['SCHEDULER_STORAGE_PATH']
        if storage_path:
            self.storage = TaskStorage(storage_path)
        
        # 注册蓝图
        blueprint = create_scheduler_blueprint(self)
        app.register_blueprint(blueprint, url_prefix='/_internal')
        
        # 设置实例
        with self._instance_lock:
            Scheduler._instance = self
        
        # 启动调度器
        if self._enabled and self._autostart:
            self.start()
        
        logger.info(f"Flask Scheduler initialized (enabled={self._enabled}, autostart={self._autostart})")
    
    def start(self) -> None:
        """启动调度器"""
        if not self._enabled:
            logger.warning("Scheduler is disabled, cannot start")
            return
        
        if self.is_running():
            logger.warning("Scheduler is already running")
            return
        
        self._stop_event.clear()
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        logger.info("Flask Scheduler started")
    
    def stop(self) -> None:
        """停止调度器"""
        if not self.is_running():
            return
        
        logger.info("Stopping Flask Scheduler...")
        self._stop_event.set()
        
        # 等待调度线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        # 关闭执行器
        if self._executor:
            self._executor.shutdown(wait=True)
        
        # 取消所有运行中的任务
        for future in self._running_tasks.values():
            if not future.done():
                future.cancel()
        self._running_tasks.clear()
        
        logger.info("Flask Scheduler stopped")
    
    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return (self._thread is not None and 
                self._thread.is_alive() and 
                not self._stop_event.is_set())
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.storage.add_task(task)
        logger.debug(f"Task '{task.name}' added to scheduler")
    
    def remove_task(self, name: str) -> bool:
        """移除任务"""
        # 取消运行中的任务
        if name in self._running_tasks:
            future = self._running_tasks[name]
            if not future.done():
                future.cancel()
            del self._running_tasks[name]
        
        return self.storage.remove_task(name)
    
    def get_task(self, name: str) -> Optional[Task]:
        """获取任务"""
        return self.storage.get_task(name)
    
    def get_all_tasks(self) -> list:
        """获取所有任务"""
        return self.storage.get_all_tasks()
    
    def run_task(self, name: str) -> bool:
        """手动运行任务"""
        task = self.get_task(name)
        if not task:
            logger.error(f"Task '{name}' not found")
            return False
        
        if not task.enabled:
            logger.warning(f"Task '{name}' is disabled")
            return False
        
        if task.status == TaskStatus.RUNNING:
            logger.warning(f"Task '{name}' is already running")
            return False
        
        # 提交任务到线程池
        self._submit_task(task, force_run=True)
        return True
    
    def _run_scheduler(self) -> None:
        """调度器主循环"""
        logger.info("Scheduler thread started")
        
        while not self._stop_event.is_set():
            try:
                self._check_and_run_tasks()
                time.sleep(self._tick_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(self._tick_interval)
        
        logger.info("Scheduler thread stopped")
    
    def _check_and_run_tasks(self) -> None:
        """检查并运行到期任务"""
        now = datetime.now()
        tasks = self.storage.get_all_tasks()
        
        for task in tasks:
            if not task.enabled:
                continue
            
            if task.status == TaskStatus.RUNNING:
                continue
            
            if self._should_run_task(task, now):
                self._submit_task(task)
    
    def _should_run_task(self, task: Task, now: datetime) -> bool:
        """检查任务是否应该运行"""
        # 延迟任务
        if task.task_type == TaskType.DELAY:
            if task.next_run_at is None:
                # 首次运行
                task.next_run_at = now + task.delay
                return False
            return now >= task.next_run_at
        
        # 间隔任务
        if task.task_type == TaskType.INTERVAL:
            if task.next_run_at is None:
                # 首次运行
                task.next_run_at = now
                return True
            return now >= task.next_run_at
        
        # Cron任务
        if task.task_type == TaskType.CRON:
            try:
                parser = CronParser(task.cron_expression)
                if task.next_run_at is None:
                    # 首次运行
                    task.next_run_at = parser.get_next_run_time(now)
                    return False
                return now >= task.next_run_at
            except Exception as e:
                logger.error(f"Error parsing cron for task '{task.name}': {e}")
                return False
        
        return False
    
    def _submit_task(self, task: Task, force_run: bool = False) -> None:
        """提交任务到线程池"""
        if not self._executor:
            logger.error("Task executor not available")
            return
        
        # 生成运行ID
        run_id = str(uuid.uuid4())
        task.current_run_id = run_id
        task.status = TaskStatus.RUNNING
        task.last_run_at = datetime.now()
        
        # 更新下次运行时间
        if not force_run:
            self._update_next_run_time(task)
        
        # 提交到线程池
        future = self._executor.submit(self._execute_task, task, run_id)
        self._running_tasks[task.name] = future
        
        # 添加完成回调
        future.add_done_callback(
            lambda f: self._task_completed(task.name, run_id, f)
        )
        
        logger.debug(f"Task '{task.name}' submitted (run_id: {run_id})")
    
    def _execute_task(self, task: Task, run_id: str) -> Any:
        """执行任务"""
        logger.info(f"Executing task '{task.name}' (run_id: {run_id})")
        start_time = datetime.now()
        
        try:
            # 执行任务函数
            if self.app:
                with self.app.app_context():
                    result = task.func()
            else:
                result = task.func()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 更新指标
            self.storage.update_task_metrics(
                task.name, duration, success=True
            )
            
            logger.info(f"Task '{task.name}' completed successfully in {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            # 更新指标
            self.storage.update_task_metrics(
                task.name, duration, success=False, error=error_msg
            )
            
            logger.error(f"Task '{task.name}' failed after {duration:.2f}s: {error_msg}")
            raise TaskError(f"Task execution failed: {error_msg}") from e
    
    def _task_completed(self, task_name: str, run_id: str, future: Future) -> None:
        """任务完成回调"""
        try:
            # 移除运行记录
            if task_name in self._running_tasks:
                del self._running_tasks[task_name]
            
            # 获取任务
            task = self.get_task(task_name)
            if not task:
                return
            
            # 更新状态
            if future.exception():
                task.status = TaskStatus.FAILED
                task.last_error = str(future.exception())
                logger.error(f"Task '{task_name}' failed: {future.exception()}")
            else:
                task.status = TaskStatus.SUCCESS
                task.last_error = None
                task.retry_count = 0
            
            task.current_run_id = None
            
        except Exception as e:
            logger.error(f"Error in task completion handler: {e}")
    
    def _update_next_run_time(self, task: Task) -> None:
        """更新任务下次运行时间"""
        now = datetime.now()
        
        if task.task_type == TaskType.INTERVAL:
            task.next_run_at = now + task.interval
        
        elif task.task_type == TaskType.CRON:
            try:
                parser = CronParser(task.cron_expression)
                task.next_run_at = parser.get_next_run_time(now)
            except Exception as e:
                logger.error(f"Error updating cron next run time for '{task.name}': {e}")
        
        elif task.task_type == TaskType.DELAY:
            # 延迟任务只运行一次，禁用任务
            task.enabled = False
            task.next_run_at = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取调度器指标"""
        return self.storage.get_metrics_summary()
    
    def reload(self) -> None:
        """重新加载调度器配置"""
        logger.info("Reloading scheduler configuration...")
        
        # 这里可以实现配置重新加载逻辑
        # 目前只是重启调度器
        was_running = self.is_running()
        
        if was_running:
            self.stop()
        
        # 重新初始化
        if self.app:
            self.init_app(self.app)
        elif was_running:
            self.start()
        
        logger.info("Scheduler configuration reloaded")