"""Tests of the diagnostics of the Integration Blueprint integration."""

from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant.typing import ClientSessionGenerator
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
    init_integration: MockConfigEntry,
) -> None:
    """Test the diagnostics redact the API key and the MAC address."""
    assert (
        await get_diagnostics_for_config_entry(hass, hass_client, init_integration)
        == snapshot
    )
