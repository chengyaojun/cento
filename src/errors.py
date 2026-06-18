class CentoError(Exception):
    def __init__(self, message, data=None):
        super().__init__(message)
        self.message = message
        self.data = data

    def __str__(self):
        return self.message
