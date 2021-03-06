import re
from datetime import datetime

import pymongo
from bson import ObjectId
from marshmallow import Schema, fields, validate
from pytz import UTC

from exceptions import InvalidDataException
from models import User, Event, SOURCES, EventCategory
from utils import get_random_color
from validators import ObjectIdSchemaValidator


class UserSchema(Schema):
    name = fields.String(required=True)
    username = fields.String(required=True, validate=[validate.Regexp(regex=r'^[a-z0-9]+$', flags=re.IGNORECASE)])
    password = fields.String(required=True)

    def __init__(self, data, **kwargs):
        super(UserSchema, self).__init__(**kwargs)
        self.data, self.errors = self.load(data)

    def save(self, user=None):
        if self.errors and len(self.errors) > 0:
            raise InvalidDataException(message='Invalid user input fields', fields=self.errors)
        if not user:
            user = User()
        user.name = self.data.get('name')
        user.username = self.data.get('username')
        user.set_password(self.data.get('password'))
        try:
            user.save()
            return user
        except pymongo.errors.DuplicateKeyError:
            raise InvalidDataException(message='Invalid user input fields', fields={
                'username': ['Username must be unique']
            })


class ScoreSchema(Schema):
    usefulness = fields.Integer(required=True, validate=[validate.Range(min=1, max=10)])
    pleasure = fields.Integer(required=True, validate=[validate.Range(min=1, max=10)])
    fatigue = fields.Integer(required=True, validate=[validate.Range(min=1, max=10)])


class CategorySchema(Schema):
    id = fields.String(required=True, validate=[ObjectIdSchemaValidator()])
    name = fields.String(required=True)


class EventLocationSchema(Schema):
    longitude = fields.Float(required=True)
    latitude = fields.Float(required=True)


class EventSchema(Schema):
    category = fields.Nested(CategorySchema, required=False)
    name = fields.String(required=True)
    start_date = fields.DateTime(required=True)
    location = fields.Nested(EventLocationSchema, required=False)
    finish_date = fields.DateTime(required=True)
    result_score = fields.Nested(ScoreSchema, required=False)
    source_type = fields.Integer(required=True, validate=[validate.Range(min=-1, max=len(SOURCES) - 2)])
    color = fields.String(required=False)

    def __init__(self, data=None, **kwargs):
        super(EventSchema, self).__init__(**kwargs)
        if data is not None:
            self.data, self.errors = self.load(data)

    def save(self, user, event=None):
        if self.errors and len(self.errors) > 0:
            raise InvalidDataException(message='Invalid event input fields', fields=self.errors)
        if event is None:
            event = Event()
        # TODO add check on correct category (it must exist and be either current_user's or default (created on server)
        event.category = self.data.get('category')

        event.name = self.data.get('name')
        event.start_date = self.data.get('start_date')
        # if not event.start_date.tzinfo:
        #     event.start_date = UTC.localize(event.start_date)
        # else:
        #     event.start_date = event.start_date.astimezone(UTC)
        event.finish_date = self.data.get('finish_date')
        # if not event.finish_date.tzinfo:
        #     event.finish_date = UTC.localize(event.finish_date)
        # else:
        #     event.finish_date = event.finish_date.astimezone(UTC)
        event.result_score = self.data.get('result_score')
        event.source_type = self.data.get('source_type')
        event.location = self.data.get('location')
        event.user = user.id
        event.color = self.data.get('color')
        event.save()
        return event


def save_category(data, user, category=None):
    name = data.get('name', None)
    if not name:
        raise InvalidDataException(message='Invalid event category field format',
                                   fields={
                                       'name': ['Missing or empty field']
                                   })
    if not category:
        category = EventCategory()
    category.name = name
    category.user = user.id
    try:
        category.save()
    except pymongo.errors.DuplicateKeyError:
        raise InvalidDataException(message='Invalid event category input data', fields={
            'name': ['Must be unique for user']
        })
    return category


class LocationSchema(Schema):
    longitude = fields.Float(load_from='long', required=True)
    latitude = fields.Float(load_from='lat', required=True)
