# Generated by Django 3.0.5 on 2020-11-02 14:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0051_auto_20201102_1444'),
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilescheduleinfo',
            name='profile',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_info', to='data.UserProfile'),
        ),
    ]