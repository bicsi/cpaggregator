from django.views import generic

from info import models
from info.tables import ResultsTable


class ResultsDetailView(generic.DetailView):
    template_name = 'info/results_detail.html'
    model = models.TaskSheet
    slug_url_kwarg = 'slice_id'
    slug_field = 'slice_id'
    table = None

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        submissions = obj.get_best_submissions()
        self.table = ResultsTable(submissions)
        print(submissions)
        return obj

    def get_context_data(self, **kwargs):
        print(kwargs)
        kwargs['table'] = self.table
        return super().get_context_data(**kwargs)
