"""Django's DB sessions with authenticated encryption for MFA enrollment material."""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore


class SessionStore(DatabaseSessionStore):
    def encode(self, session_dict):
        signed = super().encode(session_dict)
        return Fernet(settings.SESSION_ENCRYPTION_KEY.encode()).encrypt(signed.encode()).decode()

    def decode(self, session_data):
        try:
            signed = Fernet(settings.SESSION_ENCRYPTION_KEY.encode()).decrypt(session_data.encode())
        except (InvalidToken, ValueError, TypeError):
            return {}
        return super().decode(signed.decode())
