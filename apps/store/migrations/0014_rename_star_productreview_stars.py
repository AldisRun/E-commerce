# Generated by Django 5.1.4 on 2025-02-08 12:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_productreview'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productreview',
            old_name='star',
            new_name='stars',
        ),
    ]
