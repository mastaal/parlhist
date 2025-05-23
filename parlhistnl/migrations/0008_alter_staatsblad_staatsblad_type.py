# Generated by Django 5.0.6 on 2025-02-05 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parlhistnl", "0007_alter_handeling_options_alter_kamerstuk_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="staatsblad",
            name="staatsblad_type",
            field=models.CharField(
                choices=[
                    ("Wet", "Wet"),
                    ("Rijkswet", "Rijkswet"),
                    ("AMvB", "Amvb"),
                    ("RijksAMvB", "Rijksamvb"),
                    ("Verbeterblad", "Verbeterblad"),
                    ("Onbekend", "Onbekend"),
                    ("Klein Koninklijk Besluit", "Kkb"),
                ],
                default="Onbekend",
                max_length=256,
            ),
        ),
    ]
