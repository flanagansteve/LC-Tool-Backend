# Generated by Django 3.0.3 on 2020-06-30 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0039_lc_believable_price_of_goods_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitallc',
            name='hts_code',
            field=models.CharField(default='', max_length=12),
        ),
    ]
