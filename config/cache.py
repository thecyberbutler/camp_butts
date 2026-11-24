from django.utils.crypto import salted_hmac


def private_cache_key(key, key_prefix, version):
    # Allauth's TOTP replay keys contain one-time codes. Persist only a keyed digest.
    return salted_hmac(
        "campground.security-cache", f"{key_prefix}:{version}:{key}", algorithm="sha256"
    ).hexdigest()
