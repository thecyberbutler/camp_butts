import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import (
    IntegrityError,
    OperationalError,
    close_old_connections,
    connections,
    transaction,
)
from psycopg.types.range import Range

from apps.accounts.models import User
from apps.campsites.models import Campsite
from apps.notifications.models import Notification
from apps.reservations.models import Occupancy
from apps.reservations.services import BookingError, block, book, modify

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency]


def race(*functions):
    from apps.tenancy.context import current_tenant, tenant_scope

    tenant = current_tenant()
    barrier = Barrier(len(functions))

    def run(function):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            with tenant_scope(tenant):
                return function()
        except (BookingError, IntegrityError):
            return "rejected"
        except OperationalError as error:
            # PostgreSQL may abort a participant of simultaneous direct exclusion
            # inserts as a deadlock victim. Only that specific safe outcome counts.
            if getattr(error.__cause__, "sqlstate", None) == "40P01":
                return "rejected"
            raise
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(functions)) as pool:
        return list(pool.map(run, functions))


def reserve(user_id, site_id, dates, key=None):
    return str(
        book(
            actor=User.objects.get(pk=user_id),
            campsite_id=site_id,
            start=dates[0],
            end=dates[1],
            submission_key=key or uuid.uuid4(),
        ).pk
    )


def test_simultaneous_overlapping_reservations(camper, other, site, dates):
    results = race(
        lambda: reserve(camper.pk, site.pk, dates), lambda: reserve(other.pk, site.pk, dates)
    )
    assert results.count("rejected") == 1
    assert Occupancy.objects.count() == Notification.objects.count() == 1


def test_simultaneous_reservation_and_block(camper, staff, site, dates):
    results = race(
        lambda: reserve(camper.pk, site.pk, dates),
        lambda: str(
            block(
                actor=User.objects.get(pk=staff.pk),
                campsite_id=site.pk,
                start=dates[0],
                end=dates[1],
                reason="Repairs",
                submission_key=uuid.uuid4(),
            ).pk
        ),
    )
    assert results.count("rejected") == 1
    assert Occupancy.objects.count() == 1


def test_simultaneous_duplicate_submission(camper, site, dates):
    key = uuid.uuid4()
    results = race(
        lambda: reserve(camper.pk, site.pk, dates, key),
        lambda: reserve(camper.pk, site.pk, dates, key),
    )
    assert results[0] == results[1] != "rejected"
    assert Occupancy.objects.count() == Notification.objects.count() == 1


def test_simultaneous_account_limit(camper, site, dates, policy):
    policy.max_active = 1
    policy.multiple_sites = True
    policy.save()
    second = Campsite.objects.create(name="Pine 2", site_type=site.site_type)
    results = race(
        lambda: reserve(camper.pk, site.pk, dates), lambda: reserve(camper.pk, second.pk, dates)
    )
    assert results.count("rejected") == 1
    assert Occupancy.objects.count() == 1


def test_constraint_authoritative_without_service_locks(camper, other, site, dates):
    def insert(user):
        with transaction.atomic():
            return str(
                Occupancy.objects.create(
                    campsite_id=site.pk,
                    camper_id=user.pk,
                    dates=Range(*dates),
                    created_by_id=user.pk,
                    modified_by_id=user.pk,
                    submission_key=uuid.uuid4(),
                    request_fingerprint="0" * 64,
                ).pk
            )

    results = race(lambda: insert(camper), lambda: insert(other))
    assert results.count("rejected") == 1
    assert Occupancy.objects.count() == 1


def test_simultaneous_modifications_cannot_overlap(camper, other, site, dates):
    first = reserve(camper.pk, site.pk, dates)
    second_dates = (dates[1] + timedelta(days=2), dates[1] + timedelta(days=4))
    second = reserve(other.pk, site.pk, second_dates)
    target = (dates[1] + timedelta(days=6), dates[1] + timedelta(days=8))
    results = race(
        lambda: str(
            modify(
                actor=User.objects.get(pk=camper.pk),
                reservation_id=first,
                start=target[0],
                end=target[1],
            ).pk
        ),
        lambda: str(
            modify(
                actor=User.objects.get(pk=other.pk),
                reservation_id=second,
                start=target[0],
                end=target[1],
            ).pk
        ),
    )
    assert results.count("rejected") == 1
    assert Occupancy.objects.filter(dates__overlap=Range(*target)).count() == 1
