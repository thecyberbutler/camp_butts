from django.db import migrations


def initialize(apps, schema_editor):
    apps.get_model("configuration", "Campground").objects.get_or_create(pk=1)
    for name in ("Camper", "Staff", "Administrator"):
        apps.get_model("auth", "Group").objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("configuration", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [
        migrations.RunPython(initialize, migrations.RunPython.noop),
        migrations.RunSQL(
            (
                "CREATE TABLE security_cache (cache_key varchar(255) PRIMARY KEY, val"
                "ue text NOT NULL, expires timestamp with time zone NOT NULL); CREATE"
                " INDEX security_cache_expires ON security_cache (expires);"
            ),
            "DROP TABLE security_cache;",
        ),
    ]
