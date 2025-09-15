from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

# Falls du die optionalen Helper-Binary-Sensoren nutzt, bleibt BINARY_SENSOR drin.
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entry and reload on options changes."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    # Bei Options-Änderungen sauber neu laden
    entry.async_on_unload(entry.add_update_listener(_update_listener))

    # Plattformen starten
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration on any options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration entry."""
    # WICHTIG: Nur (entry, PLATFORMS) übergeben – nicht 'hass' zusätzlich!
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
