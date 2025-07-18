# Generated by Django 5.2.2 on 2025-06-10 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parlhistnl", "0011_remove_handeling_vergadering_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="handeling",
            name="ondernummer",
        ),
        migrations.AddField(
            model_name="handeling",
            name="preferred_url",
            field=models.URLField(default=""),
        ),
        migrations.AddField(
            model_name="handeling",
            name="raw_xml",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="handeling",
            name="sru_record_xml",
            field=models.BinaryField(default=b""),
        ),
        migrations.AddField(
            model_name="handeling",
            name="vergaderjaar",
            field=models.CharField(default="", max_length=9),
        ),
    ]
