"""Config flow of the Integration Blueprint integration."""

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    BlueprintApiClient,
    BlueprintAuthError,
    BlueprintConnectionError,
    BlueprintDevice,
)
from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import BlueprintConfigEntry

_LOGGER = logging.getLogger(__name__)

API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_API_KEY): API_KEY_SELECTOR,
    }
)
REAUTH_SCHEMA = vol.Schema({vol.Optional(CONF_API_KEY): API_KEY_SELECTOR})
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
            NumberSelectorConfig(
                min=5, max=3600, mode=NumberSelectorMode.BOX, unit_of_measurement="s"
            )
        ),
    }
)


async def _async_get_device(
    hass: HomeAssistant, config: Mapping[str, Any]
) -> tuple[BlueprintDevice | None, dict[str, str]]:
    """Connect to the device, returning it or the errors of the form."""
    client = BlueprintApiClient(
        async_get_clientsession(hass),
        config[CONF_HOST],
        config[CONF_PORT],
        config.get(CONF_API_KEY),
    )
    try:
        return await client.async_get_device(), {}
    except BlueprintAuthError:
        return None, {"base": "invalid_auth"}
    except BlueprintConnectionError:
        return None, {"base": "cannot_connect"}
    except Exception:
        _LOGGER.exception("Unexpected error while connecting to the device")
        return None, {"base": "unknown"}


class BlueprintConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow of the integration."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a device."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device, errors = await _async_get_device(self.hass, user_input)
            if device:
                await self.async_set_unique_id(format_mac(device.mac))
                self._abort_if_unique_id_configured(updates=user_input)
                return self.async_create_entry(
                    title=f"{device.model} {user_input[CONF_HOST]}", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                CONNECTION_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle an API key rejected by the device."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new API key."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            device, errors = await _async_get_device(
                self.hass, {**entry.data, CONF_API_KEY: user_input.get(CONF_API_KEY)}
            )
            if device:
                await self.async_set_unique_id(format_mac(device.mac))
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_KEY: user_input.get(CONF_API_KEY)}
                )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=REAUTH_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the connection settings of the device."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            device, errors = await _async_get_device(self.hass, user_input)
            if device:
                await self.async_set_unique_id(format_mac(device.mac))
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(entry, data=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONNECTION_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: BlueprintConfigEntry,
    ) -> BlueprintOptionsFlow:
        """Return the options flow."""
        return BlueprintOptionsFlow()


class BlueprintOptionsFlow(OptionsFlowWithReload):
    """Options of the integration, the entry is reloaded when they change."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
