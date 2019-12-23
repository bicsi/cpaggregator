from core.logging import log
from info.models import Task


def fix_task_ids():
    for task in Task.objects.select_related("judge").all():

        log.info(f"OLD TASK ID: {task.task_id}")
        if task.judge.judge_id == "cf":
            task.task_id = task.task_id.replace("_", "/")
        if task.judge.judge_id == "ac":
            if "/" in task.task_id:
                contest_id, task_id = task.task_id.split('/')
            else:
                contest_id, _ = task.task_id.rsplit('_', 1)
                task_id = task.task_id
            task.task_id = "/".join([contest_id.replace("_", "-"), task_id])
        log.info(f"NEW TASK ID: {task.task_id}")
        task.save()
