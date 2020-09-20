import datetime
import random

from django.utils import timezone

from core.logging import log
from data.models import UserHandle, Submission, Task
from ladders.models import LadderTask
from stats.services import compute_ladder_statistics


def generate_new_task(ladder, commit=True):
    profile = ladder.profile
    log.info(f"Generating new task for {profile}...")

    handles = list(UserHandle.objects.filter(user=profile).select_related('judge'))
    judges = {handle.judge for handle in handles}

    tried_tasks = set(Submission.objects
                      .filter(author__in=handles)
                      .values_list('task', flat=True)
                      .distinct())
    previous_tasks = set(ladder.tasks.values_list('task', flat=True))
    forbidden_tasks = tried_tasks | previous_tasks

    available_tasks = [
        task for task in Task.objects
            .filter(judge__in=judges, statistics__isnull=False)
            .select_related('statistics')
        if task.pk not in forbidden_tasks
           and task.statistics.users_solved_count >= 2]

    if not available_tasks:
        log.warning("Could not generate: no tasks to choose from.")
        return None

    solved_tasks_scores = [
        score for _, score in Submission.objects
            .filter(author__in=handles, verdict='AC')
            .values_list('task', 'task__statistics__difficulty_score')
            .distinct()
        if score is not None]

    bounds = 25, 60
    if len(solved_tasks_scores) >= 25:
        solved_tasks_scores.sort()
        solved_tasks_scores = solved_tasks_scores[-50:-5]
        mid_score = random.choice(solved_tasks_scores)
        bounds = mid_score * 0.9, mid_score * 1.1

    if profile.user.username == "adrian.budau":
        bounds[0] *= 1.5
        bounds[1] *= 1.5

    sought_score = random.randint(int(bounds[0]), int(bounds[1]))
    log.info(f"Sought score: {sought_score} (bounds: {bounds})")

    random.shuffle(available_tasks)
    best_error, chosen_task = None, None
    for task in available_tasks:
        curr_error = abs(task.statistics.difficulty_score - sought_score)
        if not chosen_task or best_error > curr_error:
            best_error, chosen_task = curr_error, task

    log.info(f"Chosen task: {chosen_task} (score: {chosen_task.statistics.difficulty_score})")
    duration = datetime.timedelta(minutes=120)
    ladder_task = LadderTask(
        ladder=ladder,
        task=chosen_task,
        duration=duration,
        status=LadderTask.Status.NEW)

    if commit:
        ladder_task.save()
    return ladder_task


def update_ladder(ladder):
    profile = ladder.profile
    ladder_tasks = list(LadderTask.objects.filter(ladder=ladder).select_related('task', 'task__statistics'))

    next_level = 1 + len(ladder_tasks)
    current_level = (next_level
                     if not ladder_tasks or ladder_tasks[-1].is_finished
                     else next_level - 1)

    current_task = None
    if current_level != next_level:
        current_task = ladder_tasks[-1]

        # Check if it was expired or solved
        ac_submissions = list(
            Submission.objects
                .filter(task=current_task.task,
                        author__user=profile,
                        verdict='AC')
                .order_by('submitted_on')[:1])
        if ac_submissions and (not current_task.started_on or
                               current_task.started_on + current_task.duration >
                               ac_submissions[0].submitted_on):
            current_task.status = LadderTask.Status.COMPLETED
            current_task.save()
            current_level += 1
        elif (current_task.started_on and current_task.started_on +
              current_task.duration < timezone.now()):
            current_task.status = LadderTask.Status.EXPIRED
            current_task.save()
            current_level += 1

    if current_level == next_level:
        current_task = generate_new_task(ladder)
        if current_task:
            ladder_tasks.append(current_task)
            next_level += 1
        compute_ladder_statistics()

    return ladder_tasks, current_task