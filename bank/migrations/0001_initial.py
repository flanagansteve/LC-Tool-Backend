# Generated by Django 3.0.3 on 2020-03-20 02:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('using_digital_app', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LCAppQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.CharField(max_length=250)),
                ('key', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=25)),
                ('required', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='BankEmployee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=250, null=True)),
                ('title', models.CharField(blank=True, max_length=250, null=True)),
                ('email', models.CharField(max_length=50)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.Bank')),
            ],
        ),
        migrations.AddField(
            model_name='bank',
            name='digital_application',
            field=models.ManyToManyField(to='bank.LCAppQuestion'),
        ),
    ]
