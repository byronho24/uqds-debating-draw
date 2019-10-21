# Generated by Django 2.1.7 on 2019-04-04 02:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0030_auto_20190324_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='score',
            name='score',
            field=models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(1)]),
        ),
    ]