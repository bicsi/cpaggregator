# Generated by Django 2.1.2 on 2018-12-10 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskstatistics',
            name='favorited_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='taskstatistics',
            name='submission_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='taskstatistics',
            name='users_solved_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='taskstatistics',
            name='users_tried_count',
            field=models.IntegerField(default=0),
        ),
    ]