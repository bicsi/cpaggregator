# Generated by Django 2.1.2 on 2018-11-22 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0023_remove_userprofile_username'),
        ('info', '0016_tasksheet_author'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='assignment',
            unique_together={('group', 'sheet')},
        ),
    ]
