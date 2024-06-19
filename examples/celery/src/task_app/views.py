from celery.result import AsyncResult
from flask import Blueprint
from flask import request

from . import tasks

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@bp.get("/result/<id>")
def get_result(id: str) -> dict[str, object]:
    async_result = AsyncResult(id)
    ready = async_result.ready()
    return {
        "ready": ready,
        "successful": async_result.successful() if ready else None,
        "value": async_result.get() if ready else async_result.result,
    }


@bp.post("/add")
def add() -> dict[str, object]:
    a = request.form.get("a", type=int)
    b = request.form.get("b", type=int)
    task_result = tasks.add.delay(a, b)
    return {"result_id": task_result.id}


@bp.post("/block")
def block() -> dict[str, object]:
    task_result = tasks.block.delay()
    return {"result_id": task_result.id}


@bp.post("/process")
def process() -> dict[str, object]:
    task_result = tasks.process.delay(total=request.form.get("total", type=int))
    return {"result_id": task_result.id}
