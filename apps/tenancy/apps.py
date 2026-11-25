from django.apps import AppConfig


class UncachedContentTypes(dict):
    """ContentType's database-alias cache cannot distinguish PostgreSQL schemas.

    Retain its mapping interface but do not retain rows across tenant contexts.
    This favors correctness over this small framework optimization.
    """

    def __getitem__(self, key):
        return {}

    def setdefault(self, key, default=None):
        return {}


class TenancyConfig(AppConfig):
    name = "apps.tenancy"

    def ready(self):
        from django.contrib.contenttypes.models import ContentType

        ContentType.objects._cache = UncachedContentTypes()
