class NotFound(Exception):
    pass

class DiscordActionFailed(Exception):
    pass

class ConnectionIsActive(Exception):
    def __init__(self, value):
        self.value = value

class UnknownIdentification(Exception):
    def __init__(self, value):
        self.value = value

class ConnectyActionFailed(Exception):
    def __init__(self, value):
        self.value = value

class ConnectyAlreadyDone(Exception):
    def __init__(self, value):
        self.value = value