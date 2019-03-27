from datetime import datetime
import itertools

from django.utils.text import slugify

from info.models import Assignment


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


def build_group_card_context(group, user):
    return {
        "group": group,
        "is_user_member": group.members.filter(user=user).exists(),
        "assignments": [{
            "assignment": assignment,
            "solved_count": assignment.get_best_submissions().filter(
                author__user__user=user, verdict='AC').count(),
            "task_count": assignment.sheet.tasks.count(),
        } for assignment in Assignment.active.filter(group=group)[:3]],
        "assignment_count": Assignment.active.filter(group=group).count(),
        "judges": {judge for assignment in Assignment.active.filter(group=group).all()
                   for judge in assignment.get_all_judges()}
    }