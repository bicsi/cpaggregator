# Generated by Django 2.1.2 on 2019-03-27 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0023_assignment_use_best_recent'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignment',
            options={'ordering': ('ordering_id', 'assigned_on')},
        ),
        migrations.AddField(
            model_name='assignment',
            name='ordering_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
