# Generated by Django 2.1.7 on 2019-02-16 00:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0009_auto_20190216_1041'),
    ]

    operations = [
        migrations.RenameField(
            model_name='speaker',
            old_name='judge_qualification_score',
            new_name='qualification_score',
        ),
    ]
