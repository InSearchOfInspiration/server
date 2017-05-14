import json
from datetime import datetime

from bson import ObjectId
from flask import Response
from flask import request
from flask_cors import CORS
from flask_cors import cross_origin
from flask_jwt import jwt_required, current_identity
from pymodm.context_managers import no_auto_dereference

from config import JSON_MIME
from exceptions import InvalidDataException
from input_serializers import EventSchema, CategorySchema, UserSchema, save_category, LocationSchema
from models import Event, EventCategory, Location
from output_serializers import UserOutputSchema

from server import app
from utils import json_abort, place_for_location, get_brute_schedule


# CORS(app, max_age=3628800, origins='*', supports_credentials=True)

@app.route('/me/', methods=['GET', 'PUT'], strict_slashes=False)
@jwt_required()
def process_my_info():
    user = current_identity
    if 'GET' in request.method:
        schema = UserOutputSchema()
        result = schema.dump(user).data
        return Response(json.dumps(result), mimetype=JSON_MIME)
    else:
        data = request.get_json(force=True)
        if isinstance(data, str):
            data = json.loads(data)
        schema = UserSchema(data)
        try:
            schema.save(user)
            return Response("Success")
        except InvalidDataException as ex:
            return json_abort({
                'message': ex.message,
                'fields': ex.fields
            }, 400)


@app.route('/events/new/', methods=['POST'], strict_slashes=False)
@jwt_required()
def add_new_event():
    data = request.get_json(force=True)
    if isinstance(data, str):
        data = json.loads(data)
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


@app.route('/events/<string:event_id>/', methods=['PUT', 'GET', 'DELETE'], strict_slashes=False)
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
        elif 'PUT' in request.method:
            data = request.get_json(force=True)
            if isinstance(data, str):
                data = json.loads(data)
            schema = EventSchema(data)
            schema.save(current_identity, event)
            return Response("Success")
        else:
            event.delete()
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


@app.route('/categories/new/', methods=['POST'], strict_slashes=False)
@jwt_required()
def add_new_category():
    data = request.get_json(force=True)
    if isinstance(data, str):
        data = json.loads(data)
    try:
        category = save_category(data, current_identity)
        return Response(json.dumps({'id': str(category.id)}))
    except InvalidDataException as ex:
        print(ex.message, ex.fields)
        return json_abort({
            'message': ex.message,
            'fields': ex.fields
        }, 400)


@app.route('/categories/')
@jwt_required()
def get_user_categories():
    categories = EventCategory.objects.raw({
        'user': {
            '$in': [current_identity.id, None]
        }
    }).all()
    with no_auto_dereference(EventCategory):
        result = CategorySchema().dump(categories, many=True).data
        return Response(json.dumps(result), mimetype=JSON_MIME)


@app.route('/categories/id/<string:category_id>/', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def process_specific_category(category_id):
    if not ObjectId.is_valid(category_id):
        return json_abort({
            'message': 'Invalid category id'
        }, 400)
    user = current_identity
    filter_query = {'_id': ObjectId(category_id)}
    not_found_message = 'No such category'
    if 'GET' not in request.method:
        filter_query.update({
            'user': user.id
        })
        not_found_message = 'This user did not create this category to update/delete'

    try:
        category = EventCategory.objects.get(filter_query)
        if 'GET' in request.method:
            result = CategorySchema().dump(category).data
            return Response(json.dumps(result), mimetype=JSON_MIME)
        elif 'PUT' in request.method:
            data = request.get_json(force=True)
            if isinstance(data, str):
                data = json.loads(data)
            save_category(data, user, category)
        else:
            category.delete()
        return Response("Success")
    except EventCategory.DoesNotExist:
        return json_abort({
            'message': not_found_message
        }, 400)
    except InvalidDataException as ex:
        return json_abort({
            'message': ex.message,
            'fields': ex.fields
        }, 400)


@app.route('/categories/name/<string:name>/')
@jwt_required()
def get_category_by_name(name):
    try:
        category = EventCategory.objects.get({'name': name, 'user': current_identity.id})
        result = CategorySchema().dump(category).data
        return Response(json.dumps(result), mimetype=JSON_MIME)
    except EventCategory.DoesNotExist:
        return json_abort({
            'message': 'User has not category with this name'
        }, 400)


# @app.route('/me/locations/', methods=['PUT', ], strict_slashes=False)
@app.route('/coordinates/', methods=['PUT', ], strict_slashes=False)
@jwt_required()
def add_new_location_for_user():
    data = request.get_json(force=True)
    if isinstance(data, str):
        data = json.loads(data)
    schema = LocationSchema()
    data, errors = schema.load(data)
    longitude = data.get('longitude')
    latitude = data.get('latitude')
    date = datetime.utcnow()
    location = Location()
    location.longitude = longitude
    location.latitude = latitude
    location.date = date
    location.user = current_identity.id
    # place_for_location(location)
    location.save()
    return Response("Success")


@app.route('/me/locations/')
@jwt_required()
def get_my_locations():
    locations = Location.objects.raw({
        'user': current_identity.id
    }).all()
    with no_auto_dereference(Location):
        result = []
        for location in locations:
            item = {
                'longitude': location.longitude,
                'latitude': location.latitude,
                'date': str(location.date)
            }
            result.append(item)
        return Response(json.dumps(result), mimetype=JSON_MIME)


@app.route('/me/suggested_schedule/')
@jwt_required()
def get_my_suggested_schedule():
    user = current_identity
    suggested_schedule = get_brute_schedule(user)
    result = EventSchema().dump(suggested_schedule, many=True).data
    return Response(json.dumps(result), mimetype=JSON_MIME)
