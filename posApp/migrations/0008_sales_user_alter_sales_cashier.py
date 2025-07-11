# Generated by Django 5.1.3 on 2025-05-30 23:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0007_alter_product_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_as_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sales',
            name='cashier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_as_cashier', to=settings.AUTH_USER_MODEL),
        ),
    ]
