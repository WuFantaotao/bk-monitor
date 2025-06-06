# Generated by Django 3.2.25 on 2025-03-21 08:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("metadata", "0214_remove_label_bk_tenant_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="bcsclusterinfo",
            name="bk_tenant_id",
            field=models.CharField(default="system", max_length=256, null=True, verbose_name="租户ID"),
        ),
        migrations.AddField(
            model_name="eventgroup",
            name="bk_tenant_id",
            field=models.CharField(default="system", max_length=256, null=True, verbose_name="租户ID"),
        ),
        migrations.AddField(
            model_name="loggroup",
            name="bk_tenant_id",
            field=models.CharField(default="system", max_length=256, null=True, verbose_name="租户ID"),
        ),
        migrations.AddField(
            model_name="timeseriesgroup",
            name="bk_tenant_id",
            field=models.CharField(default="system", max_length=256, null=True, verbose_name="租户ID"),
        ),
    ]
