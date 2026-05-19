"""Platform for Crestron Switch integration."""

import asyncio
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchEntity
from homeassistant.util import slugify
from homeassistant.const import CONF_NAME, CONF_DEVICE_CLASS

from .const import (
    HUB,
    DOMAIN,
    CONF_SWITCH_ON_JOIN,
    CONF_SWITCH_OFF_JOIN,
    CONF_SWITCH_STATE_JOIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Required(CONF_SWITCH_ON_JOIN): cv.positive_int,
        vol.Required(CONF_SWITCH_OFF_JOIN): cv.positive_int,
        vol.Required(CONF_SWITCH_STATE_JOIN): cv.positive_int,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    hub = hass.data[DOMAIN][HUB]
    async_add_entities([CrestronSwitch(hub, config)])


class CrestronSwitch(SwitchEntity):
    def __init__(self, hub, config):
        self._hub = hub
        self._name = config.get(CONF_NAME)
        self._switch_on_join = config.get(CONF_SWITCH_ON_JOIN)
        self._switch_off_join = config.get(CONF_SWITCH_OFF_JOIN)
        self._switch_state_join = config.get(CONF_SWITCH_STATE_JOIN)
        self._device_class = config.get(CONF_DEVICE_CLASS, "switch")
        self._unique_id = slugify(f"{DOMAIN}_switch_{self._name}")

    async def async_added_to_hass(self):
        self._hub.register_callback(self.process_callback)

    async def async_will_remove_from_hass(self):
        self._hub.remove_callback(self.process_callback)

    async def process_callback(self, cbtype, value):
        if cbtype in (f"d{self._switch_state_join}", "available"):
            self.async_write_ha_state()

    @property
    def available(self):
        return self._hub.is_available()

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        return False

    @property
    def device_class(self):
        return self._device_class

    @property
    def is_on(self):
        return self._hub.get_digital(self._switch_state_join)

    @property
    def unique_id(self):
        return self._unique_id

    async def _pulse_join(self, join):
        self._hub.set_digital(join, False)
        await asyncio.sleep(0.05)
        self._hub.set_digital(join, True)
        await asyncio.sleep(0.2)
        self._hub.set_digital(join, False)

    async def async_turn_on(self, **kwargs):
        await self._pulse_join(self._switch_on_join)

    async def async_turn_off(self, **kwargs):
        await self._pulse_join(self._switch_off_join)
