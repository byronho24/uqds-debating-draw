# Generated by Django 2.1.5 on 2019-01-18 12:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fixtures', '0006_auto_20190118_1041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='winning_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='fixtures.Team'),
        ),
    ]
