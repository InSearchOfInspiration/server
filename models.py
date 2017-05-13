from pymodm import MongoModel
from pymodm import connect
from pymodm import fields
from pymongo import IndexModel, ASCENDING

from config import DB_URL
from db_validators import regex_validator


print("URL:", DB_URL)
connect(DB_URL)


class EventCategory(MongoModel):
    name = fields.CharField(required=True)

    class Meta:
        indexes = [
            IndexModel([('name', ASCENDING)], unique=True, sparse=True),
        ]

SOURCES = [
    (-1, 'unknown'),
    (0, 'desktop'),
    (1, 'mobile')
]


class User(MongoModel):
    name = fields.CharField(required=True, blank=False)
    username = fields.CharField(validators=[regex_validator(r'\w+')])
    password_hash = fields.CharField()
    target_score = fields.DictField()  # { usefulness, pleasure, fatigue }

    class Meta:
        indexes = [
            IndexModel([('username', ASCENDING)], unique=True, sparse=True)
        ]


class Event(MongoModel):
    category = fields.CharField(blank=True)
    name = fields.CharField(blank=False)
    start_date = fields.DateTimeField()
    finish_date = fields.DateTimeField()
    source_type = fields.IntegerField(choices=SOURCES)
    result_score = fields.DictField()  # { usefulness, pleasure, fatigue }
    user = fields.ReferenceField(User)
    color = fields.CharField()
