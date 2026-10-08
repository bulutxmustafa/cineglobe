"""Create the database cache table during `migrate` (plan v1.8: no Redis).

Running it here means deploys only need `migrate`; a forgotten
`createcachetable` step would otherwise break every cached request.
"""

from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    # Creates tables for every DatabaseCache in CACHES; a no-op for other backends
    # and when the table already exists.
    call_command("createcachetable", database=schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [("search", "0002_daily_counter")]

    operations = [migrations.RunPython(create_cache_table, migrations.RunPython.noop)]
