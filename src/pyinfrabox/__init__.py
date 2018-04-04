class ValidationError(Exception):
    def __init__(self, path, message):
        super(ValidationError, self).__init__("%s: %s" % (path, message))
