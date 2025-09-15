# Illuminance Plus – © 2025 Martin Kluger
# Based on clear-sky model by pnbruckner (ha-illuminance)
# License: MIT

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entry and reload on options changes."""
    # Reload, wenn Optionen geändert werden (wie bei pnbruckner)
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- Optional: globaler Dienst 'refresh_all' (einmalig registrieren) ---
    data = hass.data.setdefault(DOMAIN, {})
    entries: set[str] = data.setdefault("entries", set())
    entries.add(entry.entry_id)

    if not data.get("service_registered"):
        async def _refresh_all(call: ServiceCall) -> None:
            """Alle Illuminance-Plus-Entitäten sofort neu berechnen."""
            from homeassistant.helpers import entity_registry as er
            ent_reg = er.async_get(hass)
            entity_ids = [
                e.entity_id
                for e in ent_reg.entities.values()
                if e.platform == DOMAIN and e.domain in ("sensor", "binary_sensor")
            ]
            if entity_ids:
                await hass.services.async_call(
                    DOMAIN, "refresh", {"entity_id": entity_ids}, blocking=False
                )

        hass.services.async_register(DOMAIN, "refresh_all", _refresh_all)
        data["service_registered"] = True
    # --- Ende optionaler Dienst ---

    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration on any options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload."""
    unload_ok = await hass.config_entries.async_unload_platforms(hass, entry, PLATFORMS) \
        if hasattr(hass.config_entries, "async_unload_platforms") else \
        await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Optionalen globalen Dienst aufräumen, wenn keine Einträge mehr vorhanden sind
    data = hass.data.get(DOMAIN)
    if data:
        entries = data.get("entries")
        if isinstance(entries, set):
            entries.discard(entry.entry_id)
            if not entries and data.get("service_registered"):
                hass.services.async_remove(DOMAIN, "refresh_all")
                data["service_registered"] = False

    return unload_ok
