# Generated by Django 2.1.2 on 2019-03-28 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0031_auto_20190327_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasksource',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]