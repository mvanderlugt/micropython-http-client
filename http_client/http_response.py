from http_client.http_status import HttpStatus


class HttpResponse:
    def __init__(self, status: HttpStatus, headers: dict, body: None | bytes | dict):
        self.status = status
        self.headers = headers
        self.body = body
