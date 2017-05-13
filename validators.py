import re

import marshmallow
from bson import ObjectId
from marshmallow.validate import Validator
from pymodm.errors import ValidationError


def db_regex_validator(regex):
    pattern = re.compile(regex, re.IGNORECASE)
    message = 'Invalid string, must match regex: {0}'.format(regex)

    def validate(value):
        if not pattern.match(value):
            raise ValidationError(message)
        return True

    return validate


class ObjectIdSchemaValidator(Validator):
    def __call__(self, value):
        if not ObjectId.is_valid(str(value)):
            raise marshmallow.exceptions.ValidationError('Invalid id')
        return True
