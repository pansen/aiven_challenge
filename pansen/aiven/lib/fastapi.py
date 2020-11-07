from aiohttp import ClientResponse
from starlette.responses import Response


def as_starlette_response(_resp: ClientResponse, _body: bytes) -> Response:
    """
    Convert a `ClientResponse` and its response body to a starlette `Response`.
    """
    response = Response(content=_body, status_code=_resp.status, headers=_resp.headers)
    return response
