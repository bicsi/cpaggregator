# Generated by Django 3.0.5 on 2020-11-02 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0006_taskscheduleinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilescheduleinfo',
            name='last_updated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='taskscheduleinfo',
            name='last_updated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
