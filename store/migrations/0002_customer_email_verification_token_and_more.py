# Generated by Django 5.1.6 on 2025-02-24 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='email_verification_token',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='customer',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
