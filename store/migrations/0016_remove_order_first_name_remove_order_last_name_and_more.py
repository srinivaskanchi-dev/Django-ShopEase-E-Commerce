# Generated by Django 5.1.6 on 2025-02-26 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_order_email_order_first_name_order_last_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='phone_number',
        ),
        migrations.RemoveField(
            model_name='order',
            name='shipping_address',
        ),
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='phone',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AddField(
            model_name='order',
            name='pincode',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AddField(
            model_name='order',
            name='state',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='email',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
