"""Client of the device HTTP API.

In a real integration this client belongs to a library published on PyPI and
declared in the requirements of manifest.json and pyproject.toml.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp

REQUEST_TIMEOUT = 10


class BlueprintApiError(Exception):
    """Base error of the device API."""


class BlueprintConnectionError(BlueprintApiError):
    """The device can't be reached."""


class BlueprintAuthError(BlueprintApiError):
    """The device rejected the API key."""


class BlueprintRateLimitError(BlueprintApiError):
    """The device asks to wait before the next request."""

    def __init__(self, retry_after: int | None) -> None:
        """Initialize the error with the delay requested by the device."""
        super().__init__(f"Rate limited, retry after {retry_after} seconds")
        self.retry_after = retry_after


@dataclass(frozen=True, kw_only=True)
class BlueprintDevice:
    """Identity of the device."""

    mac: str
    model: str
    firmware: str


class BlueprintApiClient:
    """Read and control the device."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        api_key: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._base_url = f"http://{host}:{port}/api"
        self._api_key = api_key

    async def async_get_device(self) -> BlueprintDevice:
        """Return the identity of the device."""
        info = await self._request("GET", "info")
        return BlueprintDevice(
            mac=info["mac"], model=info["model"], firmware=info["firmware"]
        )

    async def async_get_data(self) -> dict[str, Any]:
        """Return the current values of the device."""
        return await self._request("GET", "data")

    async def async_set_relay(self, on: bool) -> None:
        """Switch the relay of the device."""
        await self._request("POST", "relay", {"on": on})

    async def _request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a request to the device and return the JSON response."""
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        try:
            async with (
                asyncio.timeout(REQUEST_TIMEOUT),
                self._session.request(
                    method, f"{self._base_url}/{path}", json=payload, headers=headers
                ) as response,
            ):
                if response.status in (401, 403):
                    raise BlueprintAuthError("Invalid API key")
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "")
                    raise BlueprintRateLimitError(
                        int(retry_after) if retry_after.isdigit() else None
                    )
                response.raise_for_status()
                return await response.json()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise BlueprintConnectionError(str(err) or type(err).__name__) from err
