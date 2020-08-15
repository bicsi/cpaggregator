from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from data.models import UserHandle, Submission, Task, TaskStatement, MethodTag, TaskSource, JudgeTaskStatistic, Judge
import math
from core.logging import log
from django.utils.text import slugify
from bulk_sync import bulk_sync


def write_submissions(submissions):
    submissions = list(submissions)
    # Get all handles.
    handles = {(handle.judge.judge_id, handle.handle): handle
               for handle in UserHandle.objects.filter(
                    handle__in={sub['author_id'] for sub in submissions})}
    # Get all required tasks.
    tasks = {(task.judge.judge_id, task.task_id): task
             for task in Task.objects.filter(
                task_id__in={sub['task_id'] for sub in submissions})}

    log.info("Writing submissions to database...")
    log.debug(f"TASKS: {tasks}")
    log.debug(f"HANDLES: {handles}")

    submission_models = []
    for sub in submissions:
        author = handles.get((sub['judge_id'], sub['author_id']))
        task = tasks.get((sub['judge_id'], sub['task_id']))
        if not author or not task:
            continue

        fields = dict(
            submission_id=sub['submission_id'],
            author=author,
            submitted_on=timezone.make_aware(sub['submitted_on']),
            task=task,
            verdict=sub['verdict'],
            language=sub.get('language'),
            source_size=sub.get('source_size'),
            score=sub.get('score'),
            exec_time=sub.get('exec_time'),
            memory_used=sub.get('memory_used'),
        )
        if fields['score'] and math.isnan(fields['score']):
            fields['score'] = None
        fields = {k: v for k, v in fields.items() if v is not None}
        submission_models.append(Submission(**fields))

    if submission_models:
        result = bulk_sync(submission_models,
                           key_fields=('submission_id', 'author'),
                           filters=None, skip_deletes=True)
        log.success(f"Successfully upserted {len(submission_models)} submissions! "
                    f"({result['stats']['created']} created)")
    else:
        log.info("No submissions to upsert.")


def write_tasks(tasks):
    tasks = list(tasks)
    task_tags = {tag.tag_id: tag for tag in MethodTag.objects.all()}
    judges = {judge.judge_id: judge for judge in Judge.objects.all()}

    total_created = 0
    for task_info in tasks:
        judge = judges[task_info['judge_id']]
        task, created = Task.objects.get_or_create(judge=judge, task_id=task_info['task_id'])
        if created:
            total_created += 1
        task.name = task_info['title']
        if 'statement' in task_info:
            statement, _ = TaskStatement.objects.get_or_create(task=task)
            if 'time_limit' in task_info:
                statement.time_limit_ms = task_info['time_limit']
            if 'memory_limit' in task_info:
                statement.memory_limit_kb = task_info['memory_limit']
            if 'input_file' in task_info:
                statement.input_file = task_info['input_file']
            if 'output_file' in task_info:
                statement.output_file = task_info['output_file']

            if statement.modified_by_user:
                log.info(f"Skipped updating statement for {task}: modified by user")
            else:
                statement.text = task_info['statement']
                statement.examples = task_info['examples']
            statement.save()

        for tag_id in task_info.get('tags', []):
            if tag_id in task_tags:
                task.tags.add(task_tags[tag_id])
            else:
                log.warning(f'Skipped adding tag {tag_id}. Does not exist')

        if 'source' in task_info:
            source_id = slugify(task_info['source'])
            source, _ = TaskSource.objects.get_or_create(
                judge=task.judge, source_id=source_id,
                defaults={
                    'name': task_info['source']})
            task.source = source

        task.save()
        statistic_defaults = dict(
            total_submission_count=task_info.get('total_submission_count'),
            accepted_submission_count=task_info.get('accepted_submission_count'),
            first_submitted_on=task_info.get('first_submitted_on'),
        )
        statistic_defaults = {k: v for k, v in statistic_defaults.items() if v}
        if len(statistic_defaults) > 0:
            JudgeTaskStatistic.objects.get_or_create(task=task, defaults=statistic_defaults)

    log.success(f"Successfully updated {len(tasks)} tasks! ({total_created} created)")


def write_handles(handles_info):
    handles_info = list(handles_info)
    for handle_info in handles_info:
        try:
            handle = UserHandle.objects.get(judge__judge_id=handle_info['judge_id'],
                                            handle=handle_info['handle'])
        except ObjectDoesNotExist:
            log.error(f"Can't update handle: '{handle_info['handle']}': does not exist.")
            continue

        if 'photo_url' in handle_info:
            handle.photo_url = handle_info['photo_url']
        else:
            handle.photo_url = None
        handle.save()

    log.success(f"Successfully updated {len(handles_info)} handles!")
