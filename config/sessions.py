"""Django's DB sessions with authenticated encryption for MFA enrollment material."""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore

from apps.tenancy.context import current_tenant


class SessionStore(DatabaseSessionStore):
    def encode(self, session_dict):
        signed = super().encode({"tenant": str(current_tenant().id), "data": session_dict})
        return Fernet(settings.SESSION_ENCRYPTION_KEY.encode()).encrypt(signed.encode()).decode()

    def decode(self, session_data):
        try:
            signed = Fernet(settings.SESSION_ENCRYPTION_KEY.encode()).decrypt(session_data.encode())
        except (InvalidToken, ValueError, TypeError):
            return {}
        payload = super().decode(signed.decode())
        return payload.get("data", {}) if payload.get("tenant") == str(current_tenant().id) else {}
