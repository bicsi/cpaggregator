from django import template

from ladders.models import LadderTask

register = template.Library()


@register.filter
def ladder_color(task_status):
    if task_status == LadderTask.Status.COMPLETED:
        return 'success'
    if task_status == LadderTask.Status.RUNNING:
        return 'primary'
    if task_status == LadderTask.Status.EXPIRED:
        return 'danger'
    if task_status == LadderTask.Status.LOCKED:
        return 'light'
    return 'secondary'


@register.filter
def pipe_color(task_status):
    # if task_status == LadderTask.Status.LOCKED:
    #     return 'light'
    return 'light'


@register.filter
def ladder_extra_args(task_status):
    if task_status == LadderTask.Status.LOCKED:
        return 'text-muted disabled'
    return ''


@register.filter
def ladder_icon(task_status):
    if task_status == LadderTask.Status.COMPLETED:
        return 'fa-check'
    if task_status == LadderTask.Status.RUNNING:
        return 'fa-tasks'
    if task_status == LadderTask.Status.EXPIRED:
        return 'fa-stopwatch'
    if task_status == LadderTask.Status.NEW:
        return 'fa-question'
    if task_status == LadderTask.Status.LOCKED:
        return 'fa-lock'


@register.filter()
def smooth_timedelta(timedeltaobj):
    """Convert a datetime.timedelta object into Days, Hours, Minutes, Seconds."""
    secs = timedeltaobj.total_seconds()
    timetot = ""
    if secs > 86400: # 60sec * 60min * 24hrs
        days = secs // 86400
        timetot += "{} days".format(int(days))
        secs = secs - days*86400

    if secs > 3600:
        hrs = secs // 3600
        timetot += " {} hours".format(int(hrs))
        secs = secs - hrs*3600

    if secs > 60:
        mins = secs // 60
        timetot += " {} minutes".format(int(mins))
        secs = secs - mins*60

    if secs > 0:
        timetot += " {} seconds".format(int(secs))
    return timetot