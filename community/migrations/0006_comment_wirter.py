# Generated by Django 3.2.20 on 2023-08-11 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0005_jointshipping_writer'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='wirter',
            field=models.BooleanField(default=False),
        ),
    ]