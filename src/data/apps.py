from django.apps import AppConfig

from . import populate


class DataConfig(AppConfig):
    name = 'data'

    def ready(self):
        populate.create_judges()
