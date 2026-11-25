from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from allauth.core import ratelimit
from django.db import close_old_connections, connections
from django.test import RequestFactory, override_settings

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency]


def test_parallel_rate_limit_allows_only_one_request():
    from apps.tenancy.context import current_tenant, tenant_scope

    tenant = current_tenant()
    barrier = Barrier(4)

    def consume(_):
        close_old_connections()
        try:
            request = RequestFactory().post("/test/")
            barrier.wait(timeout=10)
            with tenant_scope(tenant):
                return ratelimit.consume(request, action="probe", key="synthetic-account")
        finally:
            connections.close_all()

    with override_settings(ACCOUNT_RATE_LIMITS={"probe": "1/m/key"}):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(consume, range(4)))
    assert results.count(True) == 1
