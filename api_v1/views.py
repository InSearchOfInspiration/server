import json

from bson import ObjectId
from flask import Response
from flask import request
from flask_jwt import jwt_required, current_identity
from pymodm.context_managers import no_auto_dereference

from config import JSON_MIME
from exceptions import InvalidDataException
from input_serializers import EventSchema
from models import Event
from server import app
from utils import json_abort


@app.route('/events/new/', methods=['POST'], strict_slashes=False)
@jwt_required()
def add_new_event():
    data = request.get_json(force=True)
    schema = EventSchema(data)
    try:
        user = current_identity
        schema.save(user)
    except InvalidDataException as ex:
        return json_abort({
            'message': ex.message,
            'fields': ex.fields
        }, 400)
    return Response("Success")


def get_event_dict(event, schema=None):
    if not schema:
        schema = EventSchema()
    item = schema.dump(event).data
    item['id'] = str(event.id)
    return item


@app.route('/events/')
@jwt_required()
def get_user_events():
    user = current_identity
    events = Event.objects.raw({
        'user': user.id
    }).all()
    with no_auto_dereference(Event):
        result = []
        out_schema = EventSchema()
        for event in events:
            item = get_event_dict(event, out_schema)
            result.append(item)
        return Response(json.dumps(result), mimetype=JSON_MIME)


@app.route('/events/<string:event_id>/', methods=['PUT', 'GET'], strict_slashes=False)
@jwt_required()
def process_single_event(event_id):
    if not ObjectId.is_valid(event_id):
        return json_abort({
            'message': 'Invalid event id'
        }, 400)
    try:
        with no_auto_dereference(Event):
            event = Event.objects.get({'_id': ObjectId(event_id), 'user': current_identity.id})
        if 'GET' in request.method:
            result = get_event_dict(event)
            return Response(json.dumps(result), mimetype=JSON_MIME)
        else:
            data = request.get_json(force=True)
            schema = EventSchema(data)
            schema.save(current_identity, event)
            return Response("Success")
    except Event.DoesNotExist:
        return json_abort({
            'message': 'User has not such event'
        }, 400)
    except InvalidDataException as ex:
        return json_abort({
            'message': ex.message,
            'fields': ex.fields
        }, 400)
