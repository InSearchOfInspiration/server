import re

from pymodm.errors import ValidationError


def regex_validator(regex):
    pattern = re.compile(regex, re.IGNORECASE)
    message = 'Invalid string, must match regex: {0}'.format(regex)

    def validate(value):
        if not pattern.match(value):
            raise ValidationError(message)
        return True

    return validate
