# Generated by Django 2.1.7 on 2019-02-22 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0022_auto_20190218_2208'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='matchday',
            options={'verbose_name': 'Draw', 'verbose_name_plural': 'Draws'},
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=200, unique=True, verbose_name='Team Name'),
        ),
    ]
