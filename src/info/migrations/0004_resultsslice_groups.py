# Generated by Django 2.0.5 on 2018-10-19 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0011_auto_20181019_0416'),
        ('info', '0003_resultsslice_slice_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultsslice',
            name='groups',
            field=models.ManyToManyField(to='data.UserGroup'),
        ),
    ]
