# Generated by Django 3.0.3 on 2020-06-22 23:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0027_remove_comment_lc'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]
