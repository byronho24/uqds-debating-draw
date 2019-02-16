# Generated by Django 2.1.7 on 2019-02-16 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0015_auto_20190216_1702'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchday',
            name='attendances_competing',
            field=models.ManyToManyField(to='baseapp.Attendance'),
        ),
        migrations.AddField(
            model_name='matchday',
            name='judges',
            field=models.ManyToManyField(to='baseapp.Speaker'),
        ),
    ]
