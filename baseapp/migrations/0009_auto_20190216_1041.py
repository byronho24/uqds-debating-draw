# Generated by Django 2.1.7 on 2019-02-16 00:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0008_auto_20190216_1021'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='wins',
        ),
        migrations.AlterField(
            model_name='debate',
            name='winning_team',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='debates_won', to='baseapp.Team'),
        ),
    ]