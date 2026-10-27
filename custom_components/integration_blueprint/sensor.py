"""Sensors of the Integration Blueprint integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import BlueprintConfigEntry
from .entity import BlueprintEntity

# The coordinator fetches the data: no limit of parallel updates
PARALLEL_UPDATES = 0

STATUSES = ["idle", "running", "error"]


@dataclass(frozen=True, kw_only=True)
class BlueprintSensorEntityDescription(SensorEntityDescription):
    """Description of a sensor."""

    value_fn: Callable[[dict[str, Any]], StateType]


SENSORS: tuple[BlueprintSensorEntityDescription, ...] = (
    # Named by its device class
    BlueprintSensorEntityDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data["temperature"],
    ),
    BlueprintSensorEntityDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data["power"],
    ),
    # Named, and its states translated, by its translation key
    BlueprintSensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=STATUSES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["status"] if data["status"] in STATUSES else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueprintConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        BlueprintSensor(coordinator, description)
        for description in SENSORS
        if description.key in coordinator.data
    )


class BlueprintSensor(BlueprintEntity, SensorEntity):
    """Sensor of a device value."""

    entity_description: BlueprintSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
