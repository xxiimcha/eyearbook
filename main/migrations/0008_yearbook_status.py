# Generated by Django 5.2 on 2025-04-07 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_yearbook'),
    ]

    operations = [
        migrations.AddField(
            model_name='yearbook',
            name='status',
            field=models.CharField(default='Pending', max_length=20),
        ),
    ]
