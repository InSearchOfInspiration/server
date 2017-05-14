import json
import random
from datetime import timedelta
from functools import wraps

import numpy as np
import requests
from flask import Response
from pymodm.context_managers import no_auto_dereference
from werkzeug.exceptions import abort
from flask_jwt import current_identity

from config import JSON_MIME, GEOCODE_API_BY_LOCATION
from models import Event


def json_abort(data, status):
    abort(Response(json.dumps(data), mimetype=JSON_MIME, status=status))


def already_authenticated():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_identity:
                json_abort({
                    'message': 'User has already logged in'
                }, 400)
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def get_jwt():
    from flask import current_app
    return current_app.extensions['jwt']


def get_random_color():
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)

    return '#{0:02x}{1:02x}{2:02x}'.format(red, green, blue)


def get_probs(pdf, mu, sigma):
    return 1.0 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(pdf - mu) ** 2 / (2 * sigma ** 2))


def find_event_shorter_than_delta(events, delta, visited):
    events_copy = events[:]
    random.shuffle(events_copy)
    for event in events_copy:
        event_duration = event.finish_date - event.start_date
        if event_duration <= delta and event.id not in visited:
            return event
    return None


def get_brute_schedule(user):
    with no_auto_dereference(Event):
        users_events = list(Event.objects.raw({'user': user.id}).all())
        events = {}
        for event in users_events:
            key = event.category['name'] if event.category else 'default'
            event.duration = event.finish_date - event.start_date
            if key not in events:
                events[key] = [event]
            else:
                events[key].append(event)

    sorted_keys = []
    print('Made events')
    for _ in events:
        most_often_event_category = list(set(events.keys()) - set(sorted_keys))[0]
        for key in events:
            if len(events[key]) > len(events.get(most_often_event_category)) and key not in sorted_keys:
                most_often_event_category = key
        sorted_keys.append(most_often_event_category)

    print('Made sorted keys')

    for i in range(len(sorted_keys)):
        key = sorted_keys[i]
        sorted_keys[i] = {
            'key': key,
            'size': len(events[key])
        }

    print('Updated sorted keys')

    sizes = np.array([item['size'] for item in sorted_keys])
    mu = sizes.mean()
    sigma = sizes.var() / len(sizes)
    pdf = np.random.normal(mu, sizes.var() ** 0.5, len(sizes))
    probs = get_probs(pdf, mu, sigma)

    print('Made probs')

    hours_in_day = 15
    hours = [int(hours_in_day * prob) or 1 for prob in probs]
    if sum(hours) > hours_in_day:
        delta = sum(hours) - hours_in_day
        for i in range(len(hours)):
            if hours[i] == max(hours):
                hours[i] -= delta
                break
    hours_day_delta = timedelta(hours=hours_in_day)
    final_schedule = []

    print('Before final schedule loop')
    for hour, item in zip(hours, sorted_keys):
        key_events = events[item['key']]
        rest_hours_for_key = timedelta(hours=hour)
        hours_day_delta -= rest_hours_for_key
        visited = []
        while rest_hours_for_key.total_seconds() / 60 > 10 and len(visited) <= len(key_events):
            event = find_event_shorter_than_delta(key_events, rest_hours_for_key, visited)
            if event is None:
                hours_day_delta += rest_hours_for_key
                break
            else:
                visited.append(event.id)
                final_schedule.append(event)
                event_delta = event.finish_date - event.start_date
                rest_hours_for_key -= event_delta
        hours_day_delta += rest_hours_for_key

    print('After final schedule loop')
    if len(final_schedule) < len(users_events):
        visited = []
        rest_event = find_event_shorter_than_delta(users_events, hours_day_delta, visited)
        while rest_event is not None and len(final_schedule) <= len(users_events):
            final_schedule.append(rest_event)
            visited.append(rest_event.id)
            event_delta = rest_event.finish_date - rest_event.start_date
            hours_day_delta -= event_delta
            rest_event = find_event_shorter_than_delta(users_events, hours_day_delta, visited)

    print('Added rest events')
    random.shuffle(final_schedule)
    return final_schedule


def place_for_location(location):
    url = GEOCODE_API_BY_LOCATION.format(location.latitude, location.longitude)
    response = requests.get(url)
    places = response.json()
    if len(places['result']) == 0:
        return None
    place = places[0]
    pass
