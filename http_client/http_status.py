class HttpStatus:
    def __init__(self, version: str, code: int, reason: str):
        self.version = version
        self.code = code
        self.reason = reason
