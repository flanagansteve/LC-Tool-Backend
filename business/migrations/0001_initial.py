# Generated by Django 3.0.3 on 2020-04-01 02:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('address', models.CharField(max_length=250)),
                ('annual_cashflow', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('balance_available', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('approved_credit', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BusinessEmployee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=250, null=True)),
                ('title', models.CharField(blank=True, max_length=250, null=True)),
                ('email', models.CharField(max_length=50)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.Business')),
            ],
        ),
    ]
