"""Switch of the Integration Blueprint integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import BlueprintApiError
from .const import DOMAIN
from .coordinator import BlueprintConfigEntry
from .entity import BlueprintEntity

# Commands are sent to the device one at a time
PARALLEL_UPDATES = 1

RELAY = SwitchEntityDescription(key="relay", translation_key="relay")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueprintConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch."""
    async_add_entities([BlueprintRelay(entry.runtime_data, RELAY)])


class BlueprintRelay(BlueprintEntity, SwitchEntity):
    """Relay of the device."""

    @property
    def is_on(self) -> bool:
        """Return whether the relay is on."""
        return self.coordinator.data["relay"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the relay on."""
        await self._async_set_relay(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the relay off."""
        await self._async_set_relay(False)

    async def _async_set_relay(self, on: bool) -> None:
        """Send the command, then refresh the values."""
        try:
            await self.coordinator.client.async_set_relay(on)
        except BlueprintApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
