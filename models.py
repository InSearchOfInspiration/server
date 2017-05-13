import hashlib

from pymodm import MongoModel
from pymodm import connect
from pymodm import fields
from pymongo import IndexModel, ASCENDING
from werkzeug.security import safe_str_cmp

from config import DB_URL
from db_validators import regex_validator


print("URL:", DB_URL)
connect(DB_URL)


class EventCategory(MongoModel):
    name = fields.CharField(required=True)

    @property
    def id(self):
        return self._id

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
    username = fields.CharField(validators=[regex_validator(r'^[a-z0-9]+$')])
    password_hash = fields.CharField()
    target_score = fields.DictField(blank=True)  # { usefulness, pleasure, fatigue }

    def _get_password_hash(self, password: str) -> str:
        m = hashlib.sha256()
        m.update(password.encode('utf-8'))
        return m.digest().hex()

    def set_password(self, password: str):
        self.password_hash = self._get_password_hash(password)

    def check_password(self, password: str) -> bool:
        return safe_str_cmp(self.password_hash, self._get_password_hash(password))

    @property
    def id(self):
        return self._id

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
    user = fields.ReferenceField(User, on_delete=fields.ReferenceField.CASCADE)
    color = fields.CharField()

    @property
    def id(self):
        return self._id
