# Illuminance Plus – Helper Binary Sensors
# © 2025 Martin Kluger – MIT


from __future__ import annotations

from typing import Any, Optional

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_HELPERS_ENABLED, DEFAULT_HELPERS_ENABLED,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = {**entry.data, **entry.options}
    helpers = bool(data.get(CONF_HELPERS_ENABLED, DEFAULT_HELPERS_ENABLED))
    if not helpers:
        return

    # Haupt-Sensor anhand unique_id -> entity_id auflösen
    reg = er.async_get(hass)
    unique_id = f"{entry.entry_id}_lux"
    main_entity_id: Optional[str] = None
    for ent in reg.entities.values():
        if ent.unique_id == unique_id and ent.platform == DOMAIN:
            main_entity_id = ent.entity_id
            break
    if not main_entity_id:
        return

    name_base = data.get("name", "Illuminance Plus")
    entities: list[BinarySensorEntity] = [
        IllumPlusDarkHelper(hass, f"{name_base} – Dark", entry.entry_id, main_entity_id),
        IllumPlusDarkSoonHelper(hass, f"{name_base} – Dark soon", entry.entry_id, main_entity_id),
    ]
    async_add_entities(entities)


class _BaseAttrMirror(BinarySensorEntity):
    """Basisklasse: spiegelt ein bool-Attribut des Hauptsensors."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, name: str, entry_id: str, target_entity_id: str) -> None:
        self.hass = hass
        self._attr_name = name
        self._entry_id = entry_id
        self._target = target_entity_id
        self._attr_unique_id = f"{entry_id}_{self.__class__.__name__}"
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        # initial
        self._update_from_target()
        # live verfolgen
        self._unsub = async_track_state_change_event(
            self.hass, [self._target], self._on_target_change
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _on_target_change(self, event) -> None:
        self._update_from_target()

    def _get_attr_bool(self, key: str) -> Optional[bool]:
        st = self.hass.states.get(self._target)
        if not st:
            return None
        val = st.attributes.get(key)
        if isinstance(val, bool):
            return val
        return None

    def _update_from_target(self) -> None:
        # in abgeleiteter Klasse implementieren
        raise NotImplementedError


class IllumPlusDarkHelper(_BaseAttrMirror):
    """binary_sensor.* für is_dark"""

    def _update_from_target(self) -> None:
        val = self._get_attr_bool("is_dark")
        self._attr_is_on = bool(val) if val is not None else None
        self.async_write_ha_state()


class IllumPlusDarkSoonHelper(_BaseAttrMirror):
    """binary_sensor.* für dark_soon"""

    def _update_from_target(self) -> None:
        val = self._get_attr_bool("dark_soon")
        self._attr_is_on = bool(val) if val is not None else None
        self.async_write_ha_state()
