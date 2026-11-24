from django.core.exceptions import ValidationError


class MaximumPasswordLengthValidator:
    def validate(self, password, user=None):
        if len(password) > 256:
            raise ValidationError("Passwords may contain up to 256 characters.")

    def get_help_text(self):
        return "Use 15 to 256 characters. Password managers and pasting are supported."
