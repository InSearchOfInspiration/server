import os

DB_URL = os.environ.get('DB_URL')
if not DB_URL:
    DB_URL = "mongodb://localhost:27017/isoi-core"

JSON_MIME = 'application/json'
GOOGLE_GEOCODING_API_KEY = "AIzaSyBSEYIOZwdERPoaSazA4NjcwLryNSw4U6c"
GEOCODE_API_BY_PLACE = 'https://maps.googleapis.com/maps/api/place/details/json?placeid={0}&key=' +\
    GOOGLE_GEOCODING_API_KEY

GEOCODE_API_BY_LOCATION = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={0},{1}' \
                          '&radius=50&key=' + GOOGLE_GEOCODING_API_KEY
