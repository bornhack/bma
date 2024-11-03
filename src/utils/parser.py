"""This module contains the parsers used in the API."""

from typing import Any

import orjson
from django.http import HttpRequest
from ninja.parser import Parser
from ninja.renderers import BaseRenderer


class ORJSONParser(Parser):
    """The JSON parser for the BMA API based on orjson."""

    def parse_body(self, request: HttpRequest) -> dict[str, Any]:
        """Parse and return the request body."""
        return orjson.loads(request.body)  # type: ignore[no-any-return]


class ORJSONRenderer(BaseRenderer):
    """The JSON renderer for the BMA API based on orjson."""

    media_type = "application/json"

    def render(self, request: HttpRequest, data: dict[str, Any], *, response_status: int) -> bytes:
        """Encode the body as JSON and return."""
        return orjson.dumps(data)
