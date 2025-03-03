from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0018_update_order_numbers'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='first_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='last_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ] 