# Generated by Django 5.1.4 on 2025-02-14 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0010_alter_order_payment_intent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_intent',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
