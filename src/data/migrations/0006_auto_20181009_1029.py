# Generated by Django 2.0.5 on 2018-10-09 10:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_auto_20181009_1022'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='submission',
            name='author',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='task',
        ),
        migrations.DeleteModel(
            name='Submission',
        ),
    ]