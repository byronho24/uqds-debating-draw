# Generated by Django 2.1.5 on 2019-02-13 10:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatchDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
            ],
        ),
        migrations.RemoveField(
            model_name='debate',
            name='date',
        ),
        migrations.AddField(
            model_name='debate',
            name='match_day',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='baseapp.MatchDay'),
        ),
    ]