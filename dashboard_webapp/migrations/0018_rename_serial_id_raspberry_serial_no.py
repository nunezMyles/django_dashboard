# Generated by Django 4.1.3 on 2022-12-27 01:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard_webapp', '0017_remove_raspberry_location_flat_info_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='raspberry',
            old_name='serial_id',
            new_name='serial_no',
        ),
    ]
