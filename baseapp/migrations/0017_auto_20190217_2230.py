# Generated by Django 2.1.7 on 2019-02-17 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0016_auto_20190216_1742'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='matchday',
            name='judges',
        ),
        migrations.AddField(
            model_name='matchday',
            name='attendances_judging',
            field=models.ManyToManyField(related_name='judging_matchday', to='baseapp.Attendance'),
        ),
        migrations.AlterField(
            model_name='matchday',
            name='attendances_competing',
            field=models.ManyToManyField(related_name='competing_matchday', to='baseapp.Attendance'),
        ),
    ]
