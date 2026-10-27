"""Tests of the entities of the Integration Blueprint integration."""

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.integration_blueprint.api import BlueprintConnectionError
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

RELAY = "switch.acme_one_192_168_1_10_relay"


@pytest.mark.parametrize("platform", [Platform.SENSOR, Platform.SWITCH])
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    platform: Platform,
) -> None:
    """Test the entities and their states."""
    monkeypatch.setattr("custom_components.integration_blueprint.PLATFORMS", [platform])
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("service", "on"), [(SERVICE_TURN_ON, True), (SERVICE_TURN_OFF, False)]
)
async def test_relay(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    service: str,
    on: bool,
) -> None:
    """Test the relay commands."""
    await hass.services.async_call(
        SWITCH_DOMAIN, service, {ATTR_ENTITY_ID: RELAY}, blocking=True
    )

    mock_client.async_set_relay.assert_awaited_once_with(on)


async def test_relay_command_failed(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Test a failed command raises a translated error."""
    mock_client.async_set_relay.side_effect = BlueprintConnectionError("timeout")

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: RELAY}, blocking=True
        )
    assert err.value.translation_key == "command_failed"
