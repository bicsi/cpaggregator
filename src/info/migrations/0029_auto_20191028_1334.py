# Generated by Django 2.2.6 on 2019-10-28 13:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0028_customtasktag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='sheet',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='info.TaskSheet'),
        ),
    ]
