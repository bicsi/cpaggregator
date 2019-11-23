from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import generic

from data.models import Submission

import csv


class SubmissionDownloadCSVView(LoginRequiredMixin, generic.View):
    def get_queryset(self):
        return Submission.objects.best()

    def get_filename(self):
        return "status"

    def get(self, request, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.get_filename()}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Author', 'Task', 'Verdict', 'Score', 'Submitted on', 'Link'])
        queryset = self.get_queryset() \
            .select_related('author', 'author__user', 'task', 'task__judge')
        for submission in queryset:
            writer.writerow([
                submission.submission_id,
                submission.author.user,
                submission.task.name_or_id(),
                submission.verdict,
                submission.score or "",
                submission.submitted_on.strftime('%Y-%m-%d %H:%M:%S'),
                submission.get_url(),
            ])
        return response
