import django_tables2 as tables
import itertools

from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from data.models import Submission

class SubmissionIdColumn(tables.Column):
    def render(self, record):
        return format_html('<a href="{url}">{name}</a>',
                           url=record.get_url(), name=record.submission_id)


class AuthorColumn(tables.Column):
    def render(self, record):
        return format_html('<a href="{url}">{name}</a>',
                           url=reverse('profile', kwargs=dict(username=record.author.user.username)),
                           name=record.author.user.get_display_name())


class ResultsTable(tables.Table):
    submission_id = SubmissionIdColumn()
    author = AuthorColumn()
    submitted_on = tables.DateColumn(format='d M Y, H:i')

    class Meta:
        template_name = 'django_tables2/bootstrap-responsive.html'
        model = Submission
        exclude = ['id', 'language', 'exec_time', 'memory_used']
        sequence = ('submission_id', 'author', 'task', 'source_size', 'verdict', 'score', 'submitted_on')

    def __init__(self, *args, **kwargs):
        self.task = tables.URLColumn()
        super(ResultsTable, self).__init__(*args, **kwargs)
        self.counter = itertools.count()

    def render_task(self, value):
        return format_html('<a href="{url}">{name}</a>',
                           url=value.get_url(), name=value.name_or_id())

    def render_verdict(self, value, column):
        if value == 'Accepted':
            column.attrs = {'td': {'class': 'text-success'}}
        else:
            column.attrs = {'td': {'class': 'text-danger'}}
        return mark_safe("<strong>%s</strong>" % value)