from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from data.models import Task


@registry.register_document
class TaskDocument(Document):
    source = fields.ObjectField(properties={
        'name': fields.TextField(),
    })

    class Index:
        name = 'tasks'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Task
        fields = ['name', 'task_id']

    def get_queryset(self):
        return super(TaskDocument, self).get_queryset().select_related('source')
