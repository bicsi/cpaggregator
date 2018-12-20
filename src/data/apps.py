from django.apps import AppConfig


class DataConfig(AppConfig):
    name = 'data'

    def ready(self):
        print('READY??')
        from data import signals, tasks
