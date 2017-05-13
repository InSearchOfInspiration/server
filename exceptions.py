
class InvalidDataException(Exception):
    def __init__(self, message, fields):
        self.message = message
        self.fields = fields
