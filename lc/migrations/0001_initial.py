# Generated by Django 3.0.3 on 2020-03-11 16:50

from django.db import migrations, models
import django.db.models.deletion
import lc.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bank', '0001_initial'),
        ('business', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DigitalLC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issuer_approved', models.BooleanField()),
                ('beneficiary_approved', models.BooleanField()),
                ('terms_satisfied', models.BooleanField()),
                ('requested', models.BooleanField()),
                ('drawn', models.BooleanField()),
                ('paid_out', models.BooleanField()),
                ('credit_delivery_means', models.CharField(max_length=250)),
                ('credit_amt', models.DecimalField(decimal_places=2, max_digits=17)),
                ('currency_denomination', models.CharField(default='USD', max_length=5)),
                ('type', models.CharField(default='Commercial', max_length=20)),
                ('beneficiary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_digitallc_beneficiary', to='business.Business')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_digitallc_client', to='business.Business')),
                ('issuer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.Bank')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentaryRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_name', models.CharField(max_length=250)),
                ('required_values', models.CharField(max_length=500)),
                ('due_date', models.DateField()),
                ('link_to_submitted_doc', models.CharField(blank=True, max_length=250)),
                ('complaints', models.CharField(blank=True, max_length=1000)),
                ('satisfied', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='PdfLC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issuer_approved', models.BooleanField()),
                ('beneficiary_approved', models.BooleanField()),
                ('terms_satisfied', models.BooleanField()),
                ('requested', models.BooleanField()),
                ('drawn', models.BooleanField()),
                ('paid_out', models.BooleanField()),
                ('app_response', models.FileField(upload_to=lc.models.pdf_app_response_path)),
                ('contract', models.FileField(upload_to=lc.models.pdf_lc_contract_path)),
                ('beneficiary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_pdflc_beneficiary', to='business.Business')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_pdflc_client', to='business.Business')),
                ('issuer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.Bank')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LCAppQuestionResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_json_value', models.CharField(max_length=5000)),
                ('for_lc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lc.DigitalLC')),
                ('for_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.LCAppQuestion')),
            ],
        ),
    ]
