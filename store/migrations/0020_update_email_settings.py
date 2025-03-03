from django.db import migrations

def update_email_settings(apps, schema_editor):
    # No database changes needed
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_add_name_fields_to_order'),  # Updated to depend on your existing 0019 migration
    ]

    operations = [
        migrations.RunPython(update_email_settings),
    ]