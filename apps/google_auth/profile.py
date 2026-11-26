"""Optional registration suggestions, never verified identity or recovery factors."""

import unicodedata

import requests
from django import forms
from django.core.exceptions import ValidationError

from .constants import PEOPLE_SELF_URL
from .transport import GoogleSession


def profile_name(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if len(value) > 150 or any(unicodedata.category(char).startswith("C") for char in value):
        return ""
    return value


def profile_phone(access_token):
    if (
        not isinstance(access_token, str)
        or not 1 <= len(access_token) <= 8192
        or any(char.isspace() or ord(char) < 32 for char in access_token)
    ):
        return ""
    try:
        with GoogleSession() as session:
            response = session.get(
                PEOPLE_SELF_URL, headers={"Authorization": "Bearer " + access_token}
            )
            data = response.json()
        if not isinstance(data, dict):
            return ""
        numbers = data.get("phoneNumbers", [])
        if not isinstance(numbers, list) or len(numbers) > 20:
            return ""
        numbers = [item for item in numbers if isinstance(item, dict)]
        numbers.sort(
            key=lambda item: (
                not (
                    isinstance(item.get("metadata"), dict)
                    and item["metadata"].get("primary") is True
                )
            )
        )
        for item in numbers:
            for field in ("canonicalForm", "value"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    continue
                try:
                    return forms.RegexField(r"^[0-9+() .-]{1,32}$", max_length=32).clean(value)
                except ValidationError:
                    continue
    except (requests.RequestException, ValueError, TypeError):
        # Optional profile permission/data can be absent. Never log tokens/provider payloads
        # and never change the verified identity, account approval or authentication checks.
        return ""
    return ""
