# Generated by Django 3.0.3 on 2020-06-23 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0029_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='respondable',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]