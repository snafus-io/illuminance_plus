from __future__ import annotations
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig,
    SelectSelector, SelectSelectorConfig, SelectOptionDict,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    TextSelector,
    BooleanSelector,
)

from .const import (
    DOMAIN,
    DEFAULT_NAME, DEFAULT_MODE, DEFAULT_SCAN_SECONDS, DEFAULT_MAX_CLOUD_DIV, DEFAULT_SMOOTH_SECONDS,
    CONF_NAME, CONF_MODE, CONF_SCAN,
    CONF_WEATHER, CONF_CLOUD, CONF_PRECIP, CONF_VIS,
    CONF_ON, CONF_OFF, CONF_MAX_CLOUD_DIV, CONF_SMOOTH_SECONDS,
    CONF_DARK_SENSITIVITY, DEFAULT_DARK_SENSITIVITY,
    # NEU:
    CONF_TREND_ENABLED, CONF_TREND_WIN_5M, CONF_TREND_WIN_15M, CONF_TREND_TH_DOWN, CONF_TREND_TH_UP,
    DEFAULT_TREND_ENABLED, DEFAULT_TREND_WIN_5M, DEFAULT_TREND_WIN_15M, DEFAULT_TREND_TH_DOWN, DEFAULT_TREND_TH_UP,
    CONF_FORECAST_ENABLED, CONF_FORECAST_15M, CONF_FORECAST_30M, CONF_FORECAST_60M, CONF_DARK_SOON_MARGIN,
    DEFAULT_FORECAST_ENABLED, DEFAULT_FORECAST_15M, DEFAULT_FORECAST_30M, DEFAULT_FORECAST_60M, DEFAULT_DARK_SOON_MARGIN,
    CONF_TWILIGHT_ENABLED, DEFAULT_TWILIGHT_ENABLED,
    CONF_HELPERS_ENABLED, DEFAULT_HELPERS_ENABLED,
    CONF_WINDOWS_ENABLED, CONF_WINDOWS_YAML, CONF_GLARE_ENABLED,
    DEFAULT_WINDOWS_ENABLED, DEFAULT_WINDOWS_YAML, DEFAULT_GLARE_ENABLED,
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
        # Basis
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
            NumberSelectorConfig(min=30, max=900, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
        ),
        vol.Optional(CONF_SMOOTH_SECONDS, default=v.get(CONF_SMOOTH_SECONDS, DEFAULT_SMOOTH_SECONDS)): NumberSelector(
            NumberSelectorConfig(min=0, max=900, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
        ),
        vol.Optional(CONF_ON, default=v.get(CONF_ON, 1000)): NumberSelector(
            NumberSelectorConfig(min=0, max=10000, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="lx")
        ),
        vol.Optional(CONF_OFF, default=v.get(CONF_OFF, 3000)): NumberSelector(
            NumberSelectorConfig(min=0, max=20000, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="lx")
        ),
        vol.Optional(CONF_MAX_CLOUD_DIV, default=v.get(CONF_MAX_CLOUD_DIV, DEFAULT_MAX_CLOUD_DIV)): NumberSelector(
            NumberSelectorConfig(min=1, max=30, step=0.5, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_DARK_SENSITIVITY, default=v.get(CONF_DARK_SENSITIVITY, DEFAULT_DARK_SENSITIVITY)): NumberSelector(
            NumberSelectorConfig(min=50, max=150, step=5, unit_of_measurement="%", mode=NumberSelectorMode.SLIDER)
        ),

        # --- Trend ---
        vol.Optional(CONF_TREND_ENABLED, default=v.get(CONF_TREND_ENABLED, DEFAULT_TREND_ENABLED)): BooleanSelector(),
        vol.Optional(CONF_TREND_WIN_5M, default=v.get(CONF_TREND_WIN_5M, DEFAULT_TREND_WIN_5M)): NumberSelector(
            NumberSelectorConfig(min=3, max=30, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="min")
        ),
        vol.Optional(CONF_TREND_WIN_15M, default=v.get(CONF_TREND_WIN_15M, DEFAULT_TREND_WIN_15M)): NumberSelector(
            NumberSelectorConfig(min=5, max=60, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="min")
        ),
        vol.Optional(CONF_TREND_TH_DOWN, default=v.get(CONF_TREND_TH_DOWN, DEFAULT_TREND_TH_DOWN)): NumberSelector(
            NumberSelectorConfig(min=-2000, max=0, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="lx/min")
        ),
        vol.Optional(CONF_TREND_TH_UP, default=v.get(CONF_TREND_TH_UP, DEFAULT_TREND_TH_UP)): NumberSelector(
            NumberSelectorConfig(min=0, max=2000, step=10, mode=NumberSelectorMode.BOX, unit_of_measurement="lx/min")
        ),

        # --- Forecast ---
        vol.Optional(CONF_FORECAST_ENABLED, default=v.get(CONF_FORECAST_ENABLED, DEFAULT_FORECAST_ENABLED)): BooleanSelector(),
        vol.Optional(CONF_FORECAST_15M, default=v.get(CONF_FORECAST_15M, DEFAULT_FORECAST_15M)): BooleanSelector(),
        vol.Optional(CONF_FORECAST_30M, default=v.get(CONF_FORECAST_30M, DEFAULT_FORECAST_30M)): BooleanSelector(),
        vol.Optional(CONF_FORECAST_60M, default=v.get(CONF_FORECAST_60M, DEFAULT_FORECAST_60M)): BooleanSelector(),
        vol.Optional(CONF_DARK_SOON_MARGIN, default=v.get(CONF_DARK_SOON_MARGIN, DEFAULT_DARK_SOON_MARGIN)): NumberSelector(
            NumberSelectorConfig(min=0, max=2000, step=50, mode=NumberSelectorMode.BOX, unit_of_measurement="lx")
        ),

        # --- Twilight ---
        vol.Optional(CONF_TWILIGHT_ENABLED, default=v.get(CONF_TWILIGHT_ENABLED, DEFAULT_TWILIGHT_ENABLED)): BooleanSelector(),

        # --- Helper-Entities ---
        vol.Optional(CONF_HELPERS_ENABLED, default=v.get(CONF_HELPERS_ENABLED, DEFAULT_HELPERS_ENABLED)): BooleanSelector(),

        # --- Fenster / Blendung ---
        vol.Optional(CONF_WINDOWS_ENABLED, default=v.get(CONF_WINDOWS_ENABLED, DEFAULT_WINDOWS_ENABLED)): BooleanSelector(),
        vol.Optional(CONF_GLARE_ENABLED, default=v.get(CONF_GLARE_ENABLED, DEFAULT_GLARE_ENABLED)): BooleanSelector(),
        vol.Optional(CONF_WINDOWS_YAML, default=v.get(CONF_WINDOWS_YAML, DEFAULT_WINDOWS_YAML)): TextSelector(),
    })

class IlluminancePlusConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._name: str = "Illuminance Plus"

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
        schema = vol.Schema({vol.Required(CONF_NAME, default=self._name): str})
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
        self._name = (user_input or {}).get(CONF_NAME, "Illuminance Plus")
        return await self.async_step_options(user_input)

class IlluminancePlusOptionsFlow(OptionsFlowWithConfigEntry):
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
