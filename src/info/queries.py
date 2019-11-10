from django.db.models import QuerySet

from data.models import Judge, UserGroup
from .models import Assignment, TaskSheetTask


def get_all_judges(group: UserGroup) -> QuerySet:
    assignments = Assignment.objects.visible().filter(group=group)
    judges = TaskSheetTask.objects.filter(sheet__in=assignments.values('sheet')) \
        .values_list('task__judge', flat=True) \
        .distinct().order_by()
    return Judge.objects.filter(id__in=judges)