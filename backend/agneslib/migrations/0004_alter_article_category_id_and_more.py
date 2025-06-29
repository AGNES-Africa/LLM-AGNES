# Generated by Django 5.0.3 on 2024-03-11 04:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agneslib', '0003_negotiationstream_category_source_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='category_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='agneslib.category'),
        ),
        migrations.AlterField(
            model_name='article',
            name='negotiation_stream_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='agneslib.negotiationstream'),
        ),
        migrations.AlterField(
            model_name='category',
            name='source_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='agneslib.source'),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField()),
                ('slug', models.SlugField(blank=True, max_length=255, null=True)),
                ('negotiation_stream_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='agneslib.negotiationstream')),
                ('source_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='agneslib.source')),
            ],
        ),
    ]
