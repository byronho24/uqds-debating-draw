# Generated by Django 2.1.7 on 2019-02-16 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0010_auto_20190216_1058'),
    ]

    operations = [
        migrations.AddField(
            model_name='speaker',
            name='vetoes',
            field=models.ManyToManyField(related_name='_speaker_vetoes_+', to='baseapp.Speaker'),
        ),
    ]