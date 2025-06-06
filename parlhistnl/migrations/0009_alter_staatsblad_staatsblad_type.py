# Generated by Django 5.0.6 on 2025-02-05 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parlhistnl", "0008_alter_staatsblad_staatsblad_type"),
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
                    ("Integrale tekstplaatsing", "Integrale Tekstplaatsing"),
                ],
                default="Onbekend",
                max_length=256,
            ),
        ),
    ]
