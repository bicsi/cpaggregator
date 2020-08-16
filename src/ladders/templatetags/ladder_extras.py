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
def smooth_timedelta(timedeltaobj, fmt="long"):
    D, H, M, S = "days", "hours", "minutes", "seconds"
    if fmt == "short":
        D, H, M, S = D[0], H[0], M[0], S[0]

    """Convert a datetime.timedelta object into Days, Hours, Minutes, Seconds."""
    secs = timedeltaobj.total_seconds()
    timetot = ""
    if secs > 86400: # 60sec * 60min * 24hrs
        days = secs // 86400
        timetot += f"{int(days)} {D} "
        secs = secs - days*86400

    if secs > 3600:
        hrs = secs // 3600
        timetot += f"{int(hrs)} {H} "
        secs = secs - hrs*3600

    if secs > 60:
        mins = secs // 60
        timetot += f"{int(mins)} {M} "
        secs = secs - mins*60

    if secs > 0:
        timetot += f"{int(secs)} {S} "

    return timetot[:-1]