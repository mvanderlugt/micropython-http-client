from asyncio import sleep
from json import loads
from socket import getaddrinfo, socket
from ssl import wrap_socket

from http_client.http_response import HttpResponse
from http_client.http_status import HttpStatus


class HttpClient:
    def __init__(self, host: str, port: int, ssl: bool = False):
        self.host = host
        self.port = port
        self.ssl = ssl
        # todo connection pool?

    async def get(self, path: str, parameters: dict = None, headers: dict = None, body: bytes = b'') -> HttpResponse:
        if parameters is None:
            parameters = {}
        if headers is None:
            headers = {}
        return await self.__execute_request("GET", path, parameters, headers, body)

    async def post(self, path: str, parameters: dict = None, headers: dict = None, body: bytes = b''):
        if parameters is None:
            parameters = {}
        if headers is None:
            headers = {}
        return await self.__execute_request("POST", path, parameters, headers, body)

    async def put(self, path: str, parameters: dict = None, headers: dict = None, body: bytes = b''):
        if parameters is None:
            parameters = {}
        if headers is None:
            headers = {}
        return await self.__execute_request("PUT", path, parameters, headers, body)

    async def __execute_request(self, method: str, path: str,
                                parameters: dict,
                                request_headers: dict,
                                request_body: bytes) -> HttpResponse:
        connection = await self.__get_connection()
        if len(request_body) > 0:
            request_headers["Content-Length"] = len(request_body)
        await self.__send_head(connection, method, path, parameters, request_headers)

        if len(request_body) > 0:
            await self.__send_body(connection, request_body)

        response_status = await self.__receive_status(connection)
        response_headers = await self.__receive_response_headers(connection)
        response_body = await self.__receive_body(connection, response_headers)
        return HttpResponse(response_status, response_headers, response_body)

    async def __send_head(self, connection: socket, method: str, path: str, parameters: dict, headers: dict) -> None:
        head = []
        if len(parameters) > 0:
            path += "?"
            path += "&".join([f"{key}={value}" for key, value in parameters.items()])

        head.append(f"{method} {path} HTTP/1.0")

        head.append(f"Host: {self.host}")
        for key, value in headers.items():
            head.append(f"{key}: {value}")
        head.append("\r\n")
        head = "\r\n".join(head).encode()
        bytes_written = 0
        while bytes_written < len(head):
            bytes_written += connection.write(head[bytes_written:])
            await sleep(0)

    @staticmethod
    async def __send_body(connection, body: bytes) -> None:
        bytes_written = 0
        while bytes_written < len(body):
            bytes_written += connection.write(body[bytes_written:])
            await sleep(0)

    @staticmethod
    async def __receive_status(connection: socket) -> HttpStatus:
        status_line = None
        while status_line is None or status_line == b'':
            status_line = connection.readline()
            await sleep(0)
        status_v, status_code_s, status_rest = status_line.decode().split(" ", 2)
        return HttpStatus(status_v, int(status_code_s), status_rest.rstrip())

    @staticmethod
    async def __receive_response_headers(connection: socket) -> dict:
        response_headers = dict()
        while True:
            header_line = connection.readline()
            if not header_line or header_line == b'\r\n':
                break
            key, value = header_line.decode().split(":", 1)
            response_headers[key] = value.strip()
        return response_headers

    @staticmethod
    async def __receive_body(connection, headers) -> None | bytes | dict:
        response_body = None
        response_length = int(headers["Content-Length"])
        if response_length > 0:
            response_body = connection.read(response_length)
            while len(response_body) != response_length:
                response_body += connection.read(response_length - len(response_body))
                await sleep(0)
        content_type = headers.get("Content-Type")
        if content_type is not None and content_type.startswith("application/json"):
            response_body = loads(response_body)
        return response_body

    async def __get_connection(self) -> socket:
        _, _, _, _, socket_address = getaddrinfo(self.host, self.port)[0]
        await sleep(0)
        connection = socket()
        connection.connect(socket_address)
        connection.setblocking(False)
        if self.ssl:
            connection = wrap_socket(connection)
        return connection
