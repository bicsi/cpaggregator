# Generated by Django 2.0.5 on 2018-10-09 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='task_id',
            new_name='task',
        ),
    ]