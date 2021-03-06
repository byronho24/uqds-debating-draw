# Generated by Django 2.1.5 on 2019-02-15 09:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0004_auto_20190213_2240'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='debate',
            name='judge',
        ),
        migrations.AddField(
            model_name='debate',
            name='judges',
            field=models.ManyToManyField(to='baseapp.Speaker'),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='timestamp'),
        ),
        migrations.AlterField(
            model_name='debate',
            name='date',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
