import hashlib
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone

from apps.accounts.models import Invitation, User

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency]


def test_last_invitation_use_cannot_be_redeemed_twice(staff, policy, password):
    policy.registration_mode = "invitation"
    policy.save()
    token = secrets.token_urlsafe(32)
    invite = Invitation.objects.create(
        digest=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=1),
        max_uses=1,
        created_by=staff,
    )
    barrier = Barrier(2)

    def redeem(n):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post(
                "/c/default/accounts/signup/",
                {
                    "username": f"invited{n}",
                    "email": f"invited{n}@example.test",
                    "first_name": "Invited",
                    "last_name": "Camper",
                    "password1": password,
                    "password2": password,
                    "rules_agreed": "on",
                    "policies_agreed": "on",
                    "invitation": token,
                },
                secure=True,
            )
            return response.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(redeem, [1, 2]))
    assert statuses == [302, 302]  # Generic responses do not disclose invitation validity.
    invite.refresh_from_db()
    assert invite.uses == 1
    assert User.objects.filter(username__startswith="invited").count() == 1
