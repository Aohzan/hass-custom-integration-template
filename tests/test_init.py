"""Tests of the setup of the Integration Blueprint integration."""

from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.integration_blueprint.api import (
    BlueprintAuthError,
    BlueprintConnectionError,
    BlueprintRateLimitError,
)
from custom_components.integration_blueprint.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test the setup and unload of an entry."""
    assert init_integration.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize("method", ["async_get_device", "async_get_data"])
async def test_setup_cannot_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    method: str,
) -> None:
    """Test the setup is retried when the device is unreachable."""
    getattr(mock_client, method).side_effect = BlueprintConnectionError("timeout")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("method", ["async_get_device", "async_get_data"])
async def test_setup_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    method: str,
) -> None:
    """Test a rejected API key starts a reauth flow."""
    getattr(mock_client, method).side_effect = BlueprintAuthError
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


@pytest.mark.parametrize(
    "error", [BlueprintConnectionError("timeout"), BlueprintRateLimitError(60)]
)
async def test_update_failed(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    error: Exception,
) -> None:
    """Test the entities become unavailable when an update fails."""
    mock_client.async_get_data.side_effect = error
    freezer.tick(60)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.acme_one_192_168_1_10_power").state == (
        STATE_UNAVAILABLE
    )
