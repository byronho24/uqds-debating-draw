# Generated by Django 2.1.5 on 2019-01-23 11:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0002_auto_20190120_1314'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='debate',
            name='attendances',
        ),
        migrations.AddField(
            model_name='debate',
            name='attendance1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance1', to='baseapp.Attendance'),
        ),
        migrations.AddField(
            model_name='debate',
            name='attendance2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance2', to='baseapp.Attendance'),
        ),
    ]
