# Generated by Django 3.0.3 on 2020-07-14 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0045_merge_20200710_0259'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitallctemplate',
            name='beneficiary',
            field=models.CharField(blank=True, default='{}', max_length=1000),
        ),
    ]
