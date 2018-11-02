import sys

from data.models import Judge, UserProfile, UserHandle, Task

def create_judge(judge_id, name, homepage):
    judge, created = Judge.objects.update_or_create(
        judge_id=judge_id,
        defaults=dict(
            name=name,
            homepage=homepage
        )
    )
    print('Judge: {0}, Created: {1}'.format(str(judge), str(created)))
    return judge


def create_user(username, first_name, last_name):
    user, created = UserProfile.objects.update_or_create(
        username=username,
        defaults=dict(
            first_name=first_name,
            last_name=last_name,
        )
    )
    print('User: {0}, Created: {1}'.format(str(user), str(created)))
    return user


def create_user_handle(username, judge_id, handle):
    judge = Judge.objects.get(judge_id=judge_id)
    user = UserProfile.objects.get(username=username)

    user_handle, created = UserHandle.objects.update_or_create(
        user=user,
        judge=judge,
        defaults=dict(
            handle=handle,
        )
    )
    print('User handle: {0}, Created: {1}'.format(str(user_handle), str(created)))
    return user_handle


def create_task(task_id):
    judge_id, task_id = task_id.split(':')
    judge = Judge.objects.get(judge_id=judge_id)

    task, created = Task.objects.update_or_create(judge=judge, task_id=task_id)
    print('Task: {0}, Created: {1}'.format(str(task), str(created)))
    return task


