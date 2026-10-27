"""Base entity of the Integration Blueprint integration."""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BlueprintCoordinator


class BlueprintEntity(CoordinatorEntity[BlueprintCoordinator]):
    """Entity of a device value."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: BlueprintCoordinator, description: EntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        device = coordinator.device
        self._attr_unique_id = f"{device.mac}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.mac)},
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            manufacturer="Acme",
            name=coordinator.config_entry.title,
            model=device.model,
            sw_version=device.firmware,
        )
