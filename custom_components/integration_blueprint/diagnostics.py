"""Diagnostics of the Integration Blueprint integration."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .coordinator import BlueprintConfigEntry

TO_REDACT = {CONF_API_KEY, "mac"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BlueprintConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": {
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
        },
        "device": async_redact_data(asdict(coordinator.device), TO_REDACT),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
