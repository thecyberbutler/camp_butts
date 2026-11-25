"""Stay boundaries discovered during the first mutation-testing campaign."""

from datetime import date, datetime, timedelta

import pytest

from apps.reservations.services import BookingError, date_range


@pytest.mark.parametrize("nights", [1, 2, 89, 90])
def test_valid_stays_preserve_checkout_exclusion(nights):
    start = date(2028, 2, 28)
    end = start + timedelta(days=nights)
    result = date_range(start, end)
    assert result.lower == start and result.upper == end
    assert start in result
    assert end not in result
    assert result.lower_inc and not result.upper_inc


@pytest.mark.parametrize("nights", [-1, 0, 91, 365])
def test_invalid_lengths_return_actionable_validation(nights):
    start = date(2028, 2, 28)
    with pytest.raises(BookingError) as error:
        date_range(start, start + timedelta(days=nights))
    message = " ".join(error.value.messages).lower()
    assert "1" in message and "90" in message and "night" in message


@pytest.mark.parametrize("value", [None, "2028-02-28", True, datetime(2028, 2, 28)])
@pytest.mark.parametrize("position", ["start", "end"])
def test_non_date_values_fail_as_validation_errors(value, position):
    values = {"start": date(2028, 2, 28), "end": date(2028, 3, 1)}
    values[position] = value
    with pytest.raises(BookingError):
        date_range(**values)
