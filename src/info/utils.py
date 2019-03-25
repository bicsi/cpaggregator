from datetime import datetime
import itertools

from django.utils.text import slugify


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