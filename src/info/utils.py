from datetime import datetime
import itertools
from django.db.models import Count, Prefetch

from core.logging import log
from . import queries
from django.utils.text import slugify

from data.models import Submission, UserGroup
from info.models import Assignment, TaskSheetTask


def slugify_unique(model_klass, text, field):
    """
    Creates a slug out of a string that is unique for a given model
    Example: slugify_unique(Group, "My group", "my-group-5")
    :param model_klass: the class of the model (i.e. Group)
    :param text: the text used for slugifying (i.e. 'My group')
    :param field: the field that has to be unique (i.e. 'group_id')
    :return the slug (i.e. 'my-group-5')
    """
    max_length = model_klass._meta.get_field(field).max_length
    slug = orig = slugify(text)[:max_length]

    for x in itertools.count(1):
        if not model_klass.objects.filter(**{field: slug}).exists():
            break

        # Truncate the original slug dynamically. Minus 1 for the hyphen.
        slug = "%s-%d" % (orig[:max_length - len(str(x)) - 1], x)

    return slug


def build_group_card_context(request, groups):
    profile = request.user.profile
    member_groups = set(UserGroup.objects
                        .filter(members=profile, id__in=groups)
                        .values_list('id', flat=True))
    groups = groups.prefetch_related(Prefetch(
        'assignment_set',
        Assignment.objects.visible(),
        to_attr='visible_assignments'))

    assignments = Assignment.objects \
        .select_related('sheet') \
        .visible() \
        .filter(group__in=groups) \
        .annotate(task_count=Count('sheet__tasks'))

    tasks = TaskSheetTask.objects.filter(sheet__in=assignments.values('sheet'))
    ac_submissions = Submission.objects.best().filter(author__user=profile, verdict='AC')
    solved_tasks = tasks.filter(task__in=ac_submissions.values('task'))

    solved_count = {
        sheet['sheet']: sheet['solved_count']
        for sheet in solved_tasks.values('sheet')
                      .order_by('sheet')
                      .annotate(solved_count=Count('sheet'))}

    assignment_ctx = {
        assignment: {
                "assignment": assignment,
                "solved_count": solved_count.get(assignment.sheet.id, 0),
                "task_count": assignment.task_count}
        for assignment in assignments}

    ret = [{
            "group": group,
            "is_user_member": (group.id in member_groups),
            "assignments": [assignment_ctx[assignment]
                            for assignment in group.visible_assignments[:3]],
            "assignment_count": len(group.visible_assignments)
        } for group in groups]

    return ret


def compute_asd_scores(group):
    members = group.members.all()
    scores = {member.id: [] for member in members}
    bonuses = {member.id: 0 for member in members}
    non_bonuses = {member.id: 0 for member in members}

    for assignment in group.assignment_set.all():
        submissions = Submission.objects.best().filter(
            author__user__in=members,
            task__in=assignment.sheet.tasks.all(),
            submitted_on__gte=assignment.assigned_on,
            verdict='AC',
        ).order_by('submitted_on').all()

        bonus_given = {}
        for submission in submissions:
            bonus = bonus_given.get(submission.task.id, 0)
            if bonus < 7 and bonuses[submission.author.user.id] < 7:
                bonuses[submission.author.user.id] += 1
                bonus_given[submission.task.id] = bonus + 1
                scores[submission.author.user.id].append({
                    'submission': submission,
                    'bonus': True,
                })
            elif non_bonuses[submission.author.user.id] < 3:
                non_bonuses[submission.author.user.id] += 1
                scores[submission.author.user.id].append({
                    'submission': submission,
                    'bonus': False,
                })
    return scores


def compute_assignment_results(assignment, submissions=None):
    if submissions is None:
        submissions = assignment.get_best_submissions()

    results_data = []

    submissions_for_user_and_task = {
        (submission.author.user, submission.task): submission
        for submission in submissions}

    users = assignment.group.members.all()
    tasks = TaskSheetTask.objects.filter(sheet=assignment.sheet).all()

    for user in users:
        user_submissions = []
        has_one_submission = False
        total_score = 0
        for task in tasks:
            submission = submissions_for_user_and_task.get((user, task.task))
            if submission:
                has_one_submission = True
                if submission.verdict == 'AC':
                    total_score += task.score
            user_submissions.append(submission)
        if has_one_submission:
            results_data.append({
                'user': user,
                'results': user_submissions,
                'total_score': total_score,
            })
    results_data.sort(key=lambda x: x['total_score'], reverse=True)
    return results_data