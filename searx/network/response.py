# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring, missing-function-docstring, invalid-name, fixme

from typing import Optional, Type, Any
from types import TracebackType
import json as jsonlib

import aiohttp
import httpx._utils


class Response:
    """Look alike requests.Response from an aiohttp.ClientResponse

    Only the required methods and attributes are implemented
    """

    @classmethod
    async def new_response(cls, aiohttp_response: aiohttp.ClientResponse, stream=False) -> "Response":
        if stream:
            # streamed
            return StreamResponse(aiohttp_response)
        # not streamed
        await aiohttp_response.read()
        response = ContentResponse(aiohttp_response)
        await aiohttp_response.release()
        return response

    def __init__(self, aio_response: aiohttp.ClientResponse):
        self._aio_response = aio_response
        # TODO check if it is the original request or the last one
        self.request = aio_response.request_info
        self.url = aio_response.request_info.url
        self.ok = aio_response.status < 400
        self.cookies = aio_response.cookies
        self.headers = aio_response.headers
        self.content = aio_response._body

    @property
    def encoding(self):
        return self._aio_response.get_encoding()

    @property
    def status_code(self):
        return self._aio_response.status

    @property
    def reason_phrase(self):
        return self._aio_response.reason

    @property
    def elapsed(self):
        return 0

    @property
    def links(self):
        return self._aio_response.links

    def raise_for_status(self):
        return self._aio_response.raise_for_status()

    @property
    def history(self):
        return [
            StreamResponse(r)
            for r in self._aio_response.history
        ]

    def close(self):
        return self._aio_response.release()

    def __repr__(self) -> str:
        ascii_encodable_url = str(self.url)
        if self.reason_phrase:
            ascii_encodable_reason = self.reason_phrase.encode(
                "ascii", "backslashreplace"
            ).decode("ascii")
        else:
            ascii_encodable_reason = self.reason_phrase
        return "<{}({}) [{} {}]>".format(
                type(self).__name__, ascii_encodable_url, self.status_code, ascii_encodable_reason
        )


class ContentResponse(Response):
    """Similar to requests.Response
    """

    @property
    def text(self) -> str:
        encoding = self._aio_response.get_encoding()
        return self.content.decode(encoding, errors='strict')  # type: ignore

    def json(self, **kwargs: Any) -> Any:
        stripped = self.content.strip()  # type: ignore
        encoding = self._aio_response.get_encoding()
        if encoding is None and self.content and len(stripped) > 3:
            encoding = httpx._utils.guess_json_utf(stripped)
            if encoding is not None:
                return jsonlib.loads(self.content.decode(encoding), **kwargs)
        return jsonlib.loads(stripped.decode(encoding), **kwargs)


class StreamResponse(Response):
    """Streamed response, no .content, .text, .json()
    """

    async def __aenter__(self) -> "StreamResponse":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self._aio_response.release()

    async def iter_content(self, chunk_size=1):
        # no decode_unicode parameter
        return await self._aio_response.content.read(chunk_size)
