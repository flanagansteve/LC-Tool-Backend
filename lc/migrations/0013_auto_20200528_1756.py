# Generated by Django 3.0.3 on 2020-05-28 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0012_auto_20200528_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='digitallctemplate',
            name='template_name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]