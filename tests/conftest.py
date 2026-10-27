"""Fixtures of the Integration Blueprint tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from custom_components.integration_blueprint.api import BlueprintDevice
from custom_components.integration_blueprint.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT

HOST = "192.168.1.10"
MAC = "aa:bb:cc:dd:ee:ff"

ENTRY_DATA = {CONF_HOST: HOST, CONF_PORT: 80, CONF_API_KEY: "secret"}
DEVICE = BlueprintDevice(mac=MAC, model="Acme One", firmware="1.2.3")
DEVICE_DATA = {"temperature": 21.5, "power": 120, "status": "running", "relay": True}


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return the snapshot assertion with the Home Assistant serializer.

    Without it, syrupy serializes the registry entries with their random IDs.
    """
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable the custom integrations in every test."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the config entry of a device."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Acme One {HOST}",
        unique_id=MAC,
        data=ENTRY_DATA,
        entry_id="01JBLUEPRINT0000000000000",
    )


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Mock the API client of the device."""
    client = MagicMock()
    client.async_get_device = AsyncMock(return_value=DEVICE)
    client.async_get_data = AsyncMock(return_value=dict(DEVICE_DATA))
    client.async_set_relay = AsyncMock()
    with (
        patch(
            "custom_components.integration_blueprint.coordinator.BlueprintApiClient",
            return_value=client,
        ),
        patch(
            "custom_components.integration_blueprint.config_flow.BlueprintApiClient",
            return_value=client,
        ),
    ):
        yield client


@pytest.fixture
async def init_integration(
    hass, mock_config_entry: MockConfigEntry, mock_client: MagicMock
) -> MockConfigEntry:
    """Set up the integration."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
