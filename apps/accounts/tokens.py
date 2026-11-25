"""Keep framework token generation and bind recovery to an explicit campground."""

from allauth.account.forms import EmailAwarePasswordResetTokenGenerator

from apps.tenancy.context import current_tenant


class TenantPasswordResetTokenGenerator(EmailAwarePasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return super()._make_hash_value(user, timestamp) + ":" + str(current_tenant().id)
