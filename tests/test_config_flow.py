"""Tests of the config flow of the Integration Blueprint integration."""

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.integration_blueprint.api import (
    BlueprintAuthError,
    BlueprintConnectionError,
    BlueprintDevice,
)
from custom_components.integration_blueprint.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ENTRY_DATA, HOST, MAC

OTHER_DEVICE = BlueprintDevice(mac="11:22:33:44:55:66", model="Acme One", firmware="1")


async def test_user_flow(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test the creation of an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Acme One {HOST}"
    assert result["data"] == ENTRY_DATA
    assert result["result"].unique_id == MAC


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (BlueprintConnectionError, "cannot_connect"),
        (BlueprintAuthError, "invalid_auth"),
        (RuntimeError, "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_client: MagicMock,
    exception: type[Exception],
    error: str,
) -> None:
    """Test the connection errors, and the recovery."""
    mock_client.async_get_device.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_client.async_get_device.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Test a device can only be added once, its address is updated."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA | {CONF_HOST: "192.168.1.20"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.20"


async def test_reauth_flow(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Test a new API key can be entered."""
    result = await init_integration.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    mock_client.async_get_device.side_effect = BlueprintAuthError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "wrong"}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    mock_client.async_get_device.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert init_integration.data[CONF_API_KEY] == "new"


async def test_reconfigure_flow(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Test the connection settings can be changed."""
    result = await init_integration.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA | {CONF_HOST: "192.168.1.20", CONF_PORT: 8080}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert init_integration.data[CONF_HOST] == "192.168.1.20"
    assert init_integration.data[CONF_PORT] == 8080


async def test_reconfigure_flow_wrong_device(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Test the address of another device is refused."""
    result = await init_integration.start_reconfigure_flow(hass)
    mock_client.async_get_device.return_value = OTHER_DEVICE
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA | {CONF_HOST: "192.168.1.20"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert init_integration.data[CONF_HOST] == HOST


async def test_options_flow(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test the options reload the entry with the new update interval."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert init_integration.options == {CONF_SCAN_INTERVAL: 120}
    assert init_integration.runtime_data.update_interval.total_seconds() == 120
