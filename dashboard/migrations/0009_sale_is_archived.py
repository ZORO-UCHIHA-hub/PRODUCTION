# Generated by Django 5.2.3 on 2025-07-05 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_sale_parent_sale'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
