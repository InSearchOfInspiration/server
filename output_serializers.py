from marshmallow import Schema
from marshmallow import fields

from input_serializers import ScoreSchema


class UserOutputSchema(Schema):
    username = fields.String()
    name = fields.String()
    target_score = fields.Nested(ScoreSchema, required=False)
    id = fields.String()
