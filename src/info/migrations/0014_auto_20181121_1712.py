# Generated by Django 2.1.2 on 2018-11-21 17:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0023_remove_userprofile_username'),
        ('info', '0013_tasksheet_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_on', models.DateTimeField()),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.UserGroup')),
            ],
        ),
        migrations.RemoveField(
            model_name='tasksheet',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='tasksheet',
            name='users',
        ),
        migrations.AddField(
            model_name='tasksheet',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assignation',
            name='sheet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='info.TaskSheet'),
        ),
    ]