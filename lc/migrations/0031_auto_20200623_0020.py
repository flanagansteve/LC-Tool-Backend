# Generated by Django 3.0.3 on 2020-06-23 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0030_comment_respondable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='respondable',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]