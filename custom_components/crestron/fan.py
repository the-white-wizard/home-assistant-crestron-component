"""Platform for Crestron volume fan integration."""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)

from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.util import slugify

from .const import HUB, DOMAIN, CONF_VOLUME_JOIN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_VOLUME_JOIN): cv.positive_int,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    hub = hass.data[DOMAIN][HUB]
    async_add_entities([CrestronVolumeFan(hub, config)])


class CrestronVolumeFan(FanEntity):
    def __init__(self, hub, config):
        self._hub = hub
        self._name = config.get(CONF_NAME)
        self._volume_join = config.get(CONF_VOLUME_JOIN)
        self._unique_id = slugify(f"{DOMAIN}_volume_fan_{self._name}")

    async def async_added_to_hass(self):
        self._hub.register_callback(self.process_callback)

    async def async_will_remove_from_hass(self):
        self._hub.remove_callback(self.process_callback)

    async def process_callback(self, cbtype, value):
        if cbtype == "available" or cbtype == f"a{self._volume_join}":
            self.async_write_ha_state()

    @property
    def available(self):
        return self._hub.is_available()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def should_poll(self):
        return False

    @property
    def supported_features(self):
        return (
            FanEntityFeature.SET_SPEED
        |   FanEntityFeature.TURN_ON
        |   FanEntityFeature.TURN_OFF
        )

    @property
    def percentage(self):
        raw = self._hub.get_analog(self._volume_join)
        return round((raw / 65535) * 100)

    @property
    def is_on(self):
        return self.percentage > 0

    async def async_set_percentage(self, percentage):
        percentage = max(0, min(100, percentage))
        raw = int((percentage / 100) * 65535)
        self._hub.set_analog(self._volume_join, raw)
        self.async_write_ha_state()

    async def async_turn_on(self, percentage=None, **kwargs):
        if percentage is None:
            percentage = max(self.percentage, 1)
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        await self.async_set_percentage(0)
        
        
        
        