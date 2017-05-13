import os

DB_URL = os.environ.get('DB_URL')
if not DB_URL:
    DB_URL = "mongodb://localhost:27017/isoi-core";

