# Generated by Django 3.0.3 on 2020-06-22 23:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0026_remove_comment_author_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='lc',
        ),
    ]