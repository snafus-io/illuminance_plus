from __future__ import annotations

import math
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    UNIT_LUX,
    CONF_NAME,
    DEFAULT_NAME,
    CONF_MODE,
    DEFAULT_MODE,
    CONF_SCAN,
    DEFAULT_SCAN_SECONDS,
    CONF_SMOOTH_SECONDS,
    DEFAULT_SMOOTH_SECONDS,
    CONF_ON,
    CONF_OFF,
    CONF_WEATHER,
    CONF_CLOUD,
    CONF_PRECIP,
    CONF_VIS,
    CONF_MAX_CLOUD_DIV,
    DEFAULT_MAX_CLOUD_DIV,
    CONF_DARK_SENSITIVITY,
    DEFAULT_DARK_SENSITIVITY,
)

# ---------- kleine Helfer ----------

def _state(hass: HomeAssistant, entity_id: str | None) -> Any:
    if not entity_id:
        return None
    st = hass.states.get(entity_id)
    return None if st is None else st.state

def _attr(hass: HomeAssistant, entity_id: str | None, attr: str) -> Any:
    if not entity_id:
        return None
    st = hass.states.get(entity_id)
    return None if st is None else st.attributes.get(attr)

def _state_as_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    s = _state(hass, entity_id)
    try:
        return float(s) if s is not None else None
    except Exception:  # noqa: BLE001
        return None

def _clear_sky_lux(elev: float, mode: str) -> float:
    """Klares-Himmel-Modell (vereinfacht/pnbruckner-kompatibel)."""
    if elev <= -6:
        return 0.0
    return max(0.0, 120000.0 * math.sin(math.radians(max(0.0, elev))) ** 1.5)

def _cloud_divisor(cloud: float | None, weather: str | None, max_div: float, fallback: float) -> float:
    if cloud is None:
        return fallback
    c = max(0.0, min(100.0, float(cloud)))
    return 1.0 + (max_div - 1.0) * (c / 100.0)

def _gain_rain(mm_h: float) -> float:
    if mm_h <= 0:
        return 1.0
    return 1.0 + min(0.7, mm_h * 0.3)

def _gain_visibility(km: float, weather: str | None) -> float:
    if km >= 10:
        return 1.0
    return max(0.6, km / 10.0)

def _gain_low_sun(elev: float) -> float:
    if elev >= 10:
        return 1.0
    if elev <= 0:
        return 1.2
    return 1.0 + (10 - elev) * 0.02

DEFAULT_FALLBACK = 5.0


# --------------------------- Entity --------------------------- #
class IlluminancePlus(SensorEntity):
    """Lux-Sensor mit wetterabhängiger Dämpfung + Attributen; is_dark basiert auf geglätteter Steuergröße."""

    _attr_device_class = "illuminance"
    _attr_state_class = "measurement"
    _attr_native_unit_of_measurement = UNIT_LUX

    def __init__(self, hass: HomeAssistant, name: str, cfg: dict[str, Any], entry_id: str) -> None:
        self.hass = hass
        self._attr_name = name or DEFAULT_NAME
        self._attr_unique_id = f"{entry_id}_lux"
        self.cfg: dict[str, Any] = cfg
        self._entry_id = entry_id

        # Hysterese & Glättung
        self._is_dark: bool | None = None
        self._ema: float | None = None  # geglättete Lux für Steuerung
        self._tau: float = float(cfg.get(CONF_SMOOTH_SECONDS, DEFAULT_SMOOTH_SECONDS))
        self._scan_secs: float = float(cfg.get(CONF_SCAN, DEFAULT_SCAN_SECONDS))

        self._unsub = async_track_time_interval(
            hass, self._update, timedelta(seconds=int(self._scan_secs))
        )

    async def async_added_to_hass(self) -> None:
        await self._update(None)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _smooth(self, raw: float) -> float:
        """Exponentiell gleitender Mittelwert (EMA) über 'tau' Sekunden."""
        if self._tau is None or self._tau <= 0:
            return raw
        alpha = 1.0 - math.exp(-self._scan_secs / max(1.0, self._tau))
        if self._ema is None:
            self._ema = raw
        else:
            self._ema = (1.0 - alpha) * self._ema + alpha * raw
        return self._ema

    async def _update(self, _now) -> None:
        # >>> Optionen pro Zyklus frisch einlesen (greift sofort)
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is not None:
            self.cfg = {**entry.data, **entry.options}
            # auch Änderungen an Intervall/Glättung mitnehmen
            self._tau = float(self.cfg.get(CONF_SMOOTH_SECONDS, DEFAULT_SMOOTH_SECONDS))
            new_scan = float(self.cfg.get(CONF_SCAN, DEFAULT_SCAN_SECONDS))
            if new_scan != self._scan_secs:
                self._scan_secs = new_scan
                if self._unsub:
                    self._unsub()
                self._unsub = async_track_time_interval(
                    self.hass, self._update, timedelta(seconds=int(self._scan_secs))
                )

        # Eingaben/Sonne
        elev = float(_attr(self.hass, "sun.sun", "elevation") or -90.0)
        az_raw = _attr(self.hass, "sun.sun", "azimuth")
        try:
            az = float(az_raw) if az_raw is not None else None
        except Exception:  # noqa: BLE001
            az = None

        mode = self.cfg.get(CONF_MODE, DEFAULT_MODE)
        clear = _clear_sky_lux(elev, mode)

        weather_state = _state(self.hass, self.cfg.get(CONF_WEATHER))
        cloud_val = _state_as_float(self.hass, self.cfg.get(CONF_CLOUD))
        precip = _state_as_float(self.hass, self.cfg.get(CONF_PRECIP)) or 0.0
        vis = _state_as_float(self.hass, self.cfg.get(CONF_VIS)) or 99.0

        # Einheiten-Normalisierung
        vis_u = _attr(self.hass, self.cfg.get(CONF_VIS), "unit_of_measurement")
        if vis_u and isinstance(vis, (int, float)) and str(vis_u).lower() in ("mi", "mile", "miles"):
            vis = float(vis) * 1.60934
        pr_u = _attr(self.hass, self.cfg.get(CONF_PRECIP), "unit_of_measurement")
        if pr_u and isinstance(precip, (int, float)) and str(pr_u).lower() in ("in/h", "inch/h", "inches/hour", "in"):
            precip = float(precip) * 25.4

        # Dämpfungen
        div_cloud = _cloud_divisor(
            cloud_val, weather_state,
            float(self.cfg.get(CONF_MAX_CLOUD_DIV, DEFAULT_MAX_CLOUD_DIV)),
            DEFAULT_FALLBACK,
        )
        gain_rain = _gain_rain(precip)
        gain_vis = _gain_visibility(vis, weather_state)
        gain_low = _gain_low_sun(elev)

        # Roh-Lux (für Charts/State)
        raw_lux = 0.0 if clear <= 0 else clear / max(1.0, (div_cloud * gain_rain * gain_vis * gain_low))
        self._attr_native_value = round(raw_lux, 0)

        # Steuer-Lux (geglättet) für is_dark
        control_lux = self._smooth(raw_lux)

        # >>> Empfindlichkeit robust clampen: 5–300 %
        sens_pct = float(self.cfg.get(CONF_DARK_SENSITIVITY, DEFAULT_DARK_SENSITIVITY))
        sens_pct = max(5.0, min(300.0, sens_pct))

        on_base = float(self.cfg.get(CONF_ON, 1000))
        off_base = float(self.cfg.get(CONF_OFF, 3000))
        on_eff = on_base * (sens_pct / 100.0)
        off_eff = off_base * (sens_pct / 100.0)

        # Hysterese
        if self._is_dark is None:
            self._is_dark = (control_lux <= on_eff)
        else:
            if control_lux <= on_eff:
                self._is_dark = True
            elif control_lux >= off_eff:
                self._is_dark = False

        # Attribute
        self._attr_extra_state_attributes = {
            "is_dark": self._is_dark,
            "on_threshold": on_base,
            "off_threshold": off_base,
            "dark_sensitivity_pct": round(sens_pct, 1),
            "on_threshold_eff": round(on_eff, 0),
            "off_threshold_eff": round(off_eff, 0),
            "elevation": round(elev, 2),
            "azimuth": round(az, 1) if isinstance(az, (int, float)) else az,
            "clear_sky_lux": round(clear, 0),
            "cloud_divisor": round(div_cloud, 2),
            "rain_gain": gain_rain,
            "visibility_gain": gain_vis,
            "low_sun_gain": gain_low,
            "weather_state": weather_state,
            "cloud_input": cloud_val,
            "precip_mm_h": precip,
            "visibility_km": vis,
            "mode": mode,
            "raw_lux": round(raw_lux, 0),
            "control_lux": round(control_lux, 0),
            "smooth_seconds": self._tau,
        }

        self.async_write_ha_state()
