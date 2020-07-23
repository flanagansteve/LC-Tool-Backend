# Generated by Django 3.0.3 on 2020-06-24 22:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0034_lc_import_license_approval'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoycottLanguage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phrase', models.CharField(max_length=1000)),
                ('source', models.CharField(max_length=100)),
                ('lc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lc.LC')),
            ],
        ),
    ]