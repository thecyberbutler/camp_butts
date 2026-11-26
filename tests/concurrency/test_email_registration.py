from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client

from apps.accounts.models import User

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency]


def test_concurrent_case_variant_signups_create_one_account(password):
    barrier = Barrier(2)

    def signup(email):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post(
                "/c/default/accounts/signup/",
                {
                    "email": email,
                    "first_name": "Test",
                    "last_name": "Camper",
                    "password1": password,
                    "password2": password,
                    "rules_agreed": True,
                    "policies_agreed": True,
                },
                secure=True,
            )
            return response.status_code, response.url
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(signup, ["concurrent@example.test", "CONCURRENT@example.test"]))
    assert results == [(302, "/c/default/accounts/registration-received/")] * 2
    assert User.objects.filter(email__iexact="concurrent@example.test").count() == 1
    user = User.objects.get(email="concurrent@example.test")
    assert not user.approved and not user.is_staff and not user.is_superuser
