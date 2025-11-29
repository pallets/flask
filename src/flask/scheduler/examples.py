"""
示例任务 - 展示Flask Scheduler的功能
"""
from datetime import datetime, timedelta
import logging
from flask import current_app
from .decorators import interval_task, delay_task, cron_task


logger = logging.getLogger(__name__)


@interval_task(interval=timedelta(seconds=10), description="每10秒执行一次的示例任务")
def example_interval_task():
    """每10秒执行一次的示例任务"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[间隔任务] 当前时间: {current_time}")
        
        # 模拟一些工作
        import time
        time.sleep(0.5)
        
        logger.info(f"[间隔任务] 任务执行完成")
        return f"间隔任务执行成功: {current_time}"
        
    except Exception as e:
        logger.error(f"[间隔任务] 执行失败: {e}")
        raise


@delay_task(delay=timedelta(seconds=5), description="延迟5秒后执行的示例任务")
def example_delay_task():
    """延迟5秒后执行的示例任务"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[延迟任务] 开始执行，当前时间: {current_time}")
        
        # 模拟一些初始化工作
        import time
        time.sleep(1)
        
        logger.info(f"[延迟任务] 执行完成")
        return f"延迟任务执行成功: {current_time}"
        
    except Exception as e:
        logger.error(f"[延迟任务] 执行失败: {e}")
        raise


@cron_task(cron_expression="*/2 * * * *", description="每2分钟执行一次的cron任务")
def example_cron_task():
    """每2分钟执行一次的cron任务"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[Cron任务] 执行时间: {current_time}")
        
        # 模拟定期维护工作
        import random
        work_duration = random.uniform(0.5, 2.0)
        import time
        time.sleep(work_duration)
        
        logger.info(f"[Cron任务] 定期维护完成，耗时: {work_duration:.2f}秒")
        return f"Cron任务执行成功: {current_time} (耗时: {work_duration:.2f}秒)"
        
    except Exception as e:
        logger.error(f"[Cron任务] 执行失败: {e}")
        raise


# 额外的示例任务

@interval_task(interval=timedelta(minutes=1), description="每分钟执行的健康检查任务")
def health_check_task():
    """每分钟执行的健康检查任务"""
    try:
        # 检查应用状态
        if current_app:
            config_count = len(current_app.config)
            logger.info(f"[健康检查] 应用配置项数量: {config_count}")
        
        # 检查内存使用情况（简化版）
        import psutil
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        if memory_usage > 90:
            logger.warning(f"[健康检查] 内存使用率过高: {memory_usage}%")
        else:
            logger.info(f"[健康检查] 内存使用率正常: {memory_usage}%")
        
        return f"健康检查通过，内存使用率: {memory_usage}%"
        
    except ImportError:
        logger.info("[健康检查] psutil模块未安装，跳过内存检查")
        return "健康检查通过（基础检查）"
    except Exception as e:
        logger.error(f"[健康检查] 执行失败: {e}")
        raise


@cron_task(cron_expression="0 9 * * *", description="每天早上9点执行的数据清理任务")
def daily_cleanup_task():
    """每天早上9点执行的数据清理任务"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"[数据清理] 开始执行每日清理任务: {current_date}")
        
        # 模拟数据清理工作
        import time
        cleanup_duration = 3.0  # 模拟3秒的清理工作
        time.sleep(cleanup_duration)
        
        logger.info(f"[数据清理] 完成每日数据清理")
        return f"每日数据清理完成: {current_date}"
        
    except Exception as e:
        logger.error(f"[数据清理] 执行失败: {e}")
        raise


@delay_task(delay=timedelta(seconds=30), description="30秒后执行的初始化任务")
def initialization_task():
    """30秒后执行的初始化任务"""
    try:
        logger.info("[初始化任务] 开始执行应用初始化")
        
        # 模拟初始化工作
        import time
        time.sleep(2)
        
        # 检查调度器状态
        from .scheduler import Scheduler
        scheduler = Scheduler.get_instance()
        
        if scheduler and scheduler.is_running():
            logger.info("[初始化任务] 调度器运行正常")
            status = "调度器运行正常"
        else:
            logger.warning("[初始化任务] 调度器未运行")
            status = "调度器未运行"
        
        logger.info(f"[初始化任务] 初始化完成: {status}")
        return f"应用初始化完成: {status}"
        
    except Exception as e:
        logger.error(f"[初始化任务] 执行失败: {e}")
        raise