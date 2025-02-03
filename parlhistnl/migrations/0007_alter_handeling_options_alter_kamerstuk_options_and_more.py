# Generated by Django 5.1.5 on 2025-02-03 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parlhistnl", "0006_staatsblad_raw_xml_alter_staatsblad_staatsblad_type"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="handeling",
            options={"verbose_name_plural": "Handelingen"},
        ),
        migrations.AlterModelOptions(
            name="kamerstuk",
            options={"verbose_name_plural": "Kamerstukken"},
        ),
        migrations.AlterModelOptions(
            name="kamerstukdossier",
            options={"verbose_name_plural": "KamerstukDossiers"},
        ),
        migrations.AlterModelOptions(
            name="staatsblad",
            options={"verbose_name_plural": "Staatsbladen"},
        ),
        migrations.AlterModelOptions(
            name="vergadering",
            options={"verbose_name_plural": "Vergaderingen"},
        ),
        migrations.AddField(
            model_name="staatsblad",
            name="metadata_json",
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
    ]
