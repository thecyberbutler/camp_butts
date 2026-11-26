"""Fixed owner-approved profile scopes and self-profile endpoint (SD-029)."""

PHONE_SCOPE = "https://www.googleapis.com/auth/user.phonenumbers.read"
GOOGLE_SCOPES = ("openid", "email", "profile", PHONE_SCOPE)
PEOPLE_SELF_URL = (
    "https://people.googleapis.com/v1/people/me"
    "?personFields=phoneNumbers&sources=READ_SOURCE_TYPE_PROFILE"
)
