from django.db import migrations, models
import time
import uuid

def generate_unique_order_number(apps, schema_editor):
    Order = apps.get_model('store', 'Order')
    for order in Order.objects.all():
        if not order.order_number:
            timestamp = str(int(time.time()))[-6:]
            random_str = str(uuid.uuid4().hex)[:4]
            order.order_number = f'O{timestamp}{random_str}'
            order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0017_alter_cartitem_cart'),  # Updated to match your actual previous migration
    ]

    operations = [
        migrations.RunPython(generate_unique_order_number),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=20, unique=True),
        ),
    ] 