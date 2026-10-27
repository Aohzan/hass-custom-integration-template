"""Tests of the API client of the Integration Blueprint integration."""

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.integration_blueprint.api import (
    BlueprintApiClient,
    BlueprintAuthError,
    BlueprintConnectionError,
    BlueprintDevice,
    BlueprintRateLimitError,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

URL = "http://192.168.1.10:80/api"


@pytest.fixture
def client(hass: HomeAssistant) -> BlueprintApiClient:
    """Return a client of the device."""
    return BlueprintApiClient(
        async_get_clientsession(hass), "192.168.1.10", 80, "secret"
    )


async def test_requests(
    aioclient_mock: AiohttpClientMocker, client: BlueprintApiClient
) -> None:
    """Test the requests and their API key."""
    aioclient_mock.get(
        f"{URL}/info", json={"mac": "aa:bb", "model": "One", "firmware": "1"}
    )
    aioclient_mock.get(f"{URL}/data", json={"power": 10})
    aioclient_mock.post(f"{URL}/relay", json={})

    assert await client.async_get_device() == BlueprintDevice(
        mac="aa:bb", model="One", firmware="1"
    )
    assert await client.async_get_data() == {"power": 10}
    await client.async_set_relay(True)

    assert aioclient_mock.mock_calls[-1][2] == {"on": True}
    assert aioclient_mock.mock_calls[-1][3]["Authorization"] == "Bearer secret"


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"status": 401}, BlueprintAuthError),
        ({"status": 500}, BlueprintConnectionError),
        ({"exc": TimeoutError}, BlueprintConnectionError),
    ],
)
async def test_errors(
    aioclient_mock: AiohttpClientMocker,
    client: BlueprintApiClient,
    kwargs: dict,
    error: type[Exception],
) -> None:
    """Test the errors of the device."""
    aioclient_mock.get(f"{URL}/data", **kwargs)

    with pytest.raises(error):
        await client.async_get_data()


@pytest.mark.parametrize(("header", "retry_after"), [("30", 30), (None, None)])
async def test_rate_limited(
    aioclient_mock: AiohttpClientMocker,
    client: BlueprintApiClient,
    header: str | None,
    retry_after: int | None,
) -> None:
    """Test the delay requested by the device."""
    aioclient_mock.get(
        f"{URL}/data",
        status=429,
        headers={"Retry-After": header} if header else None,
    )

    with pytest.raises(BlueprintRateLimitError) as err:
        await client.async_get_data()
    assert err.value.retry_after == retry_after
