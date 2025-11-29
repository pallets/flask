"""
Scheduler management blueprint
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from typing import Dict, Any


def create_scheduler_blueprint(scheduler, name='scheduler'):
    """创建调度器管理蓝图"""
    bp = Blueprint(name, __name__, url_prefix='/_internal')
    
    @bp.route('/metrics', methods=['GET'])
    def get_metrics():
        """获取调度器指标"""
        try:
            metrics = scheduler.get_metrics()
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': metrics
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/tasks', methods=['GET'])
    def list_tasks():
        """获取所有任务列表"""
        try:
            tasks = scheduler.get_all_tasks()
            tasks_data = []
            
            for task in tasks:
                task_data = task.to_dict()
                # 添加运行状态
                task_data['is_running'] = task.status.value == 'running'
                task_data['scheduler_status'] = 'running' if scheduler.is_running() else 'stopped'
                tasks_data.append(task_data)
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'tasks': tasks_data,
                    'scheduler_running': scheduler.is_running(),
                    'total_tasks': len(tasks_data)
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/tasks/<task_name>', methods=['GET'])
    def get_task(task_name: str):
        """获取特定任务详情"""
        try:
            task = scheduler.get_task(task_name)
            if not task:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': f'Task "{task_name}" not found'
                }), 404
            
            task_data = task.to_dict()
            task_data['is_running'] = task.status.value == 'running'
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': task_data
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/tasks/<task_name>/run', methods=['POST'])
    def run_task(task_name: str):
        """手动运行任务"""
        try:
            success = scheduler.run_task(task_name)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Task "{task_name}" started successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': f'Failed to start task "{task_name}". Task may be disabled, already running, or not found.'
                }), 400
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/tasks/<task_name>/enable', methods=['POST'])
    def enable_task(task_name: str):
        """启用任务"""
        try:
            task = scheduler.get_task(task_name)
            if not task:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': f'Task "{task_name}" not found'
                }), 404
            
            task.enabled = True
            scheduler.storage.add_task(task)
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': f'Task "{task_name}" enabled successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/tasks/<task_name>/disable', methods=['POST'])
    def disable_task(task_name: str):
        """禁用任务"""
        try:
            task = scheduler.get_task(task_name)
            if not task:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': f'Task "{task_name}" not found'
                }), 404
            
            task.enabled = False
            scheduler.storage.add_task(task)
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': f'Task "{task_name}" disabled successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/scheduler/start', methods=['POST'])
    def start_scheduler():
        """启动调度器"""
        try:
            if scheduler.is_running():
                return jsonify({
                    'status': 'warning',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Scheduler is already running'
                })
            
            scheduler.start()
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': 'Scheduler started successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/scheduler/stop', methods=['POST'])
    def stop_scheduler():
        """停止调度器"""
        try:
            if not scheduler.is_running():
                return jsonify({
                    'status': 'warning',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Scheduler is not running'
                })
            
            scheduler.stop()
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': 'Scheduler stopped successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/scheduler/status', methods=['GET'])
    def get_scheduler_status():
        """获取调度器状态"""
        try:
            is_running = scheduler.is_running()
            tasks = scheduler.get_all_tasks()
            
            running_tasks = sum(1 for task in tasks if task.status.value == 'running')
            enabled_tasks = sum(1 for task in tasks if task.enabled)
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'scheduler_running': is_running,
                    'total_tasks': len(tasks),
                    'enabled_tasks': enabled_tasks,
                    'disabled_tasks': len(tasks) - enabled_tasks,
                    'running_tasks': running_tasks,
                    'tick_interval': scheduler._tick_interval,
                    'max_workers': scheduler._max_workers
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/reload', methods=['POST'])
    def reload_scheduler():
        """重新加载调度器配置"""
        try:
            scheduler.reload()
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': 'Scheduler configuration reloaded successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """健康检查"""
        try:
            is_running = scheduler.is_running()
            tasks = scheduler.get_all_tasks()
            
            return jsonify({
                'status': 'healthy' if is_running else 'degraded',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'scheduler_running': is_running,
                    'total_tasks': len(tasks),
                    'enabled_tasks': sum(1 for task in tasks if task.enabled)
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    return bp