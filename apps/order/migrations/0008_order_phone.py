# Generated by Django 5.1.4 on 2025-02-10 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0007_order_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='phone',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
