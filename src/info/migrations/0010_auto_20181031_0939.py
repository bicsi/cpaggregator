# Generated by Django 2.1.2 on 2018-10-31 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0009_auto_20181031_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasksheet',
            name='groups',
            field=models.ManyToManyField(blank=True, to='data.UserGroup'),
        ),
    ]
