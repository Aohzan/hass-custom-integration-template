"""Constants of the Integration Blueprint integration."""

from homeassistant.const import Platform

DOMAIN = "integration_blueprint"

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30
