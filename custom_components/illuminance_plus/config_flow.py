# Illuminance Plus – © 2025 Martin Kluger
# Based on clear-sky model by pnbruckner (ha-illuminance)
# License: MIT

from __future__ import annotations
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.core import callback
    # FlowResult-Typ ist optional, verbessert IDE-Hints
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig,
    SelectSelector, SelectSelectorConfig, SelectOptionDict,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    TextSelector,
)

from .const import (
    DOMAIN,
    DEFAULT_NAME, DEFAULT_MODE, DEFAULT_SCAN_SECONDS, DEFAULT_MAX_CLOUD_DIV, DEFAULT_SMOOTH_SECONDS,
    CONF_NAME, CONF_MODE, CONF_SCAN,
    CONF_WEATHER, CONF_CLOUD, CONF_PRECIP, CONF_VIS,
    CONF_ON, CONF_OFF, CONF_MAX_CLOUD_DIV, CONF_SMOOTH_SECONDS,
)

def _validate_thresholds(user_input: dict[str, Any]) -> str | None:
    on_thr = float(user_input.get(CONF_ON, 800))
    off_thr = float(user_input.get(CONF_OFF, 2000))
    return "thresholds" if on_thr > off_thr else None

def _build_options_schema(values: dict[str, Any] | None = None) -> vol.Schema:
    v = values or {}
    modes = [
        SelectOptionDict(value="normal", label="normal"),
        SelectOptionDict(value="simple", label="simple"),
    ]
    return vol.Schema({
        vol.Optional(CONF_NAME, default=v.get(CONF_NAME, DEFAULT_NAME)): str,
        vol.Optional(CONF_WEATHER, default=v.get(CONF_WEATHER)): EntitySelector(
            EntitySelectorConfig(domain="weather")
        ),
        vol.Optional(CONF_CLOUD, default=v.get(CONF_CLOUD)): EntitySelector(
            EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_PRECIP, default=v.get(CONF_PRECIP)): EntitySelector(
            EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_VIS, default=v.get(CONF_VIS)): EntitySelector(
            EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(CONF_MODE, default=v.get(CONF_MODE, DEFAULT_MODE)): SelectSelector(
            SelectSelectorConfig(options=modes)
        ),
        vol.Required(CONF_SCAN, default=v.get(CONF_SCAN, DEFAULT_SCAN_SECONDS)): NumberSelector(
            NumberSelectorConfig(min=30, max=900, step=10, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_SMOOTH_SECONDS, default=v.get(CONF_SMOOTH_SECONDS, DEFAULT_SMOOTH_SECONDS)): NumberSelector(
            NumberSelectorConfig(min=0, max=900, step=10, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_ON, default=v.get(CONF_ON, 1000)): NumberSelector(
            NumberSelectorConfig(min=0, max=10000, step=10, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_OFF, default=v.get(CONF_OFF, 3000)): NumberSelector(
            NumberSelectorConfig(min=0, max=20000, step=10, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_MAX_CLOUD_DIV, default=v.get(CONF_MAX_CLOUD_DIV, DEFAULT_MAX_CLOUD_DIV)): NumberSelector(
            NumberSelectorConfig(min=1, max=30, step=0.5, mode=NumberSelectorMode.BOX)
        ),
    })

class IlluminancePlusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ersteinrichtung: Name → Optionen."""
    VERSION = 1

    def __init__(self) -> None:
        self._name: str = DEFAULT_NAME

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "IlluminancePlusOptionsFlow":
        return IlluminancePlusOptionsFlow(config_entry)

    async def async_step_user(self, _user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_name()

    async def async_step_name(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            return await self.async_step_options()
        schema = vol.Schema({vol.Required(CONF_NAME, default=self._name): TextSelector()})
        return self.async_show_form(step_id="name", data_schema=schema, last_step=False)

    async def async_step_options(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            err = _validate_thresholds(user_input)
            if err:
                return self.async_show_form(
                    step_id="options", data_schema=_build_options_schema(user_input), errors={"base": err}
                )
            return self.async_create_entry(title=self._name, data={}, options=user_input)
        return self.async_show_form(step_id="options", data_schema=_build_options_schema(), last_step=True)

    async def async_step_import(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        self._name = (user_input or {}).get(CONF_NAME, DEFAULT_NAME)
        return await self.async_step_options(user_input)

class IlluminancePlusOptionsFlow(OptionsFlowWithConfigEntry):
    """⋮ → Optionen: vorhandene Werte bearbeiten."""
    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self._merged = {**entry.data, **entry.options}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            err = _validate_thresholds(user_input)
            if err:
                return self.async_show_form(
                    step_id="init", data_schema=_build_options_schema(user_input), errors={"base": err}
                )
            return self.async_create_entry(title="", data=user_input or {})
        return self.async_show_form(step_id="init", data_schema=_build_options_schema(self._merged))
