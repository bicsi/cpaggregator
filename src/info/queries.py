from data.models import Judge
from info.models import Assignment, TaskSheetTask


def get_all_judges(group):
    assignments = Assignment.objects.active().filter(group=group)
    judges = TaskSheetTask.objects.filter(sheet__in=assignments.values('sheet')) \
        .values_list('task__judge', flat=True) \
        .distinct().order_by()
    return Judge.objects.filter(id__in=judges)