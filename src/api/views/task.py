from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404

from api.serializers import TaskSerializer, TaskSerializerFull
from data.models import Task


class RetrieveTask(RetrieveAPIView):
    serializer_class = TaskSerializerFull

    def get_object(self):
        task_path = self.kwargs['task_path']
        judge_id, task_id = task_path.split('/', 1)
        return get_object_or_404(
            Task.objects.select_related('statement', 'statistics', 'judge'),
            judge__judge_id=judge_id, task_id=task_id)


class ListTasks(ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all()
