from django.utils.datetime_safe import datetime
from django.utils import timezone

from data.models import Submission


def get_month_id_from_date(date):
    return date.month - 1 + 12 * date.year


def get_date_from_month_id(month_id, format="%b-%y"):
    y, m = divmod(month_id, 12)
    return datetime(y, m + 1, 1).strftime(format)


def build_tag_stats_dict(user):
    solved_count_for_tag = {}
    for submission in Submission.best.filter(author__in=user.handles.all(), verdict='AC').all():
        for tag in submission.task.tags.all():
            solved_count_for_tag[tag] = solved_count_for_tag.get(tag, 0) + 1
    tag_stats = [{"tag": tag.tag_name, "solved_count": solved_count}
                for tag, solved_count in solved_count_for_tag.items()]

    return tag_stats


def build_activity_dict(user):
    # Build activity object.
    activity = {}

    def get_activity_item(month_id):
        return activity.get(month_id, {
            'name': get_date_from_month_id(month_id, format='%b %y'),
            'total_submission_count': 0,
            'ac_submission_count': 0,
        })

    for submission in Submission.objects.filter(author__in=user.handles.all()).all():
        month_id = get_month_id_from_date(submission.submitted_on)
        activity_item = get_activity_item(month_id)
        activity_item['total_submission_count'] += 1

        if submission.verdict == 'AC':
            activity_item['ac_submission_count'] += 1

        activity[month_id] = activity_item

    month_id_end = get_month_id_from_date(timezone.now())
    activity = [get_activity_item(month_id)
                for month_id in list(range(month_id_end - 36 + 1, month_id_end + 1))]

    return activity
