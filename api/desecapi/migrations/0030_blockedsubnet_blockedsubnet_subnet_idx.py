# Generated by Django 4.1.3 on 2023-01-27 15:58

import django.contrib.postgres.indexes
import django.core.validators
from django.db import migrations, models
import netfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ("desecapi", "0029_token_mfa"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlockedSubnet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "asn",
                    models.PositiveBigIntegerField(
                        validators=[
                            django.core.validators.MaxValueValidator(4294967295)
                        ]
                    ),
                ),
                (
                    "subnet",
                    netfields.fields.CidrAddressField(max_length=43, unique=True),
                ),
                ("country", models.TextField()),
                ("registry", models.TextField()),
                ("allocation_date", models.DateField()),
            ],
        ),
        migrations.AddIndex(
            model_name="blockedsubnet",
            index=django.contrib.postgres.indexes.GistIndex(
                fields=["subnet"], name="subnet_idx", opclasses=("inet_ops",)
            ),
        ),
    ]
