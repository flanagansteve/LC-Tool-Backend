# Generated by Django 3.0.3 on 2020-07-23 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0047_auto_20200715_0322'),
    ]

    operations = [
        migrations.AddField(
            model_name='lc',
            name='advising_type',
            field=models.IntegerField(default=0),
        ),
    ]