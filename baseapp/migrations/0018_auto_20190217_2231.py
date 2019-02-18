# Generated by Django 2.1.7 on 2019-02-17 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0017_auto_20190217_2230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchday',
            name='attendances_competing',
            field=models.ManyToManyField(related_name='competing_matchdays', to='baseapp.Attendance'),
        ),
        migrations.AlterField(
            model_name='matchday',
            name='attendances_judging',
            field=models.ManyToManyField(related_name='judging_matchdays', to='baseapp.Attendance'),
        ),
    ]