from django.views import generic
from info.views.generic import SubmissionDownloadCSVView

from data.models import Submission
from info.tables import StatusTable


class SubmissionListView(generic.ListView):
    template_name = 'info/submission_list.html'
    model = Submission
    table = None
    paginate_by = 50
    context_object_name = 'submission_list'

    queryset = Submission.objects.select_related(
        'task', 'task__judge', 'author__user', 'author__user__user')

    def get_context_data(self, *args, **kwargs):
        context = super(SubmissionListView, self) \
            .get_context_data(*args, **kwargs)

        submission_list = context.pop('submission_list')
        context['table'] = StatusTable(submission_list)
        context['submission_count'] = self.queryset.count()
        return context


class AllSubmissionsDownloadCSVView(SubmissionDownloadCSVView):
    def get_queryset(self):
        return Submission.objects.all()

