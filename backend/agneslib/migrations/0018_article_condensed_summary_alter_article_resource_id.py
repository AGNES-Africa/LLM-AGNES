# Generated by Django 5.0.3 on 2024-04-01 11:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agneslib", "0017_remove_article_size_remove_category_size_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="condensed_summary",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="resource_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="articles",
                to="agneslib.resource",
            ),
        ),
    ]
