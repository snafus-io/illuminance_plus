# Illuminance Plus – © 2025 Martin Kluger
# Based on clear-sky model by pnbruckner (ha-illuminance)
# License: MIT

from __future__ import annotations

import asyncio
import logging
import math
from math import radians, sin, cos, asin, exp
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import entity_platform

_LOGGER = logging.getLogger(__name__)

# Lux-Einheit versionssicher bestimmen
try:
    from homeassistant.const import UnitOfIlluminance  # neuere HA
    UNIT_LUX = UnitOfIlluminance.LUX
except Exception:  # noqa: BLE001
    try:
        from homeassistant.const import LIGHT_LUX  # ältere HA
        UNIT_LUX = LIGHT_LUX
    except Exception:  # noqa: BLE001
        UNIT_LUX = "lx"

DOMAIN = "illuminance_plus"

# Defaults/Keys
DEFAULT_NAME = "Illuminance Plus"
DEFAULT_MODE = "normal"
DEFAULT_SCAN_SECONDS = 120
DEFAULT_FALLBACK = 10.0
DEFAULT_MAX_CLOUD_DIV = 10.0
DEFAULT_SMOOTH_SECONDS = 180

CONF_NAME = "name"
CONF_MODE = "mode"
CONF_SCAN = "scan_seconds"
CONF_WEATHER = "weather_entity"
CONF_CLOUD = "cloud_entity"
CONF_PRECIP = "precip_entity"
CONF_VIS = "visibility_entity"
CONF_ON = "on_threshold"
CONF_OFF = "off_threshold"
CONF_MAX_CLOUD_DIV = "max_cloud_div"
CONF_SMOOTH_SECONDS = "smooth_seconds"

# NEU: Empfindlichkeit nur für is_dark (in %)
CONF_DARK_SENSITIVITY = "dark_sensitivity"
DEFAULT_DARK_SENSITIVITY = 100

WEATHER_FACTORS: dict[str, float] = {
    "exceptional": 1.0, "sunny": 1.0, "clear": 1.0,
    "partlycloudy": 2.0, "cloudy": 5.0, "rainy": 5.0,
    "pouring": 10.0, "lightning": 10.0, "lightning-rainy": 10.0, "fog": 10.0,
}

# ------------------------- Helpers ------------------------- #
def _state(hass: HomeAssistant, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    s = hass.states.get(entity_id)
    return None if s is None else s.state

def _state_as_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    s = hass.states.get(entity_id)
    if not s:
        return None
    try:
        return float(s.state)
    except (ValueError, TypeError):
        return None

def _attr(hass: HomeAssistant, entity_id: str | None, key: str) -> Any:
    if not entity_id:
        return None
    s = hass.states.get(entity_id)
    return None if s is None else s.attributes.get(key)

# --- Clear-Sky (pnb standard) + simple ---
def _clear_sky_lux_pnb(elev_deg: float) -> float:
    """Clear-sky nach pnbruckner; 0 lx ab <= -6°."""
    if elev_deg <= -6.0:
        return 0.0
    elev_rad = radians(elev_deg)
    u = sin(elev_rad)
    x = 753.66156
    s = asin(x * cos(elev_rad) / (x + 1))
    m = x * (cos(s) - u) + cos(s)
    m = exp(-0.2 * m) * u + 0.0289 * exp(-0.042 * m) * (1 + (elev_deg + 90) * u / 57.29577951)
    return 133775.0 * m

def _clear_sky_lux_simple(elev_deg: float) -> float:
    return 0.0 if elev_deg <= -6.0 else 1000.0 * max(0.0, sin(radians(max(0.0, elev_deg))))

def _clear_sky_lux(elev_deg: float, mode: str) -> float:
    if mode == "simple":
        return _clear_sky_lux_simple(elev_deg)
    return _clear_sky_lux_pnb(elev_deg)  # pnb als Standard

def _cloud_divisor(cloud_value: float | None, weather_state: str | None, max_div: float, fallback: float) -> float:
    if isinstance(cloud_value, (int, float)):
        div = pow(10.0, max(0.0, min(100.0, float(cloud_value))) / 100.0)
        return min(div, max_div)
    if isinstance(cloud_value, str) and cloud_value.isdigit():
        val = float(cloud_value)
        div = pow(10.0, max(0.0, min(100.0, val)) / 100.0)
        return min(div, max_div)
    if weather_state:
        return WEATHER_FACTORS.get(weather_state, fallback)
    return fallback

def _gain_rain(mm_h: float | None) -> float:
    v = 0.0 if mm_h is None else mm_h
    if v >= 2.0: return 2.2
    if v >= 0.5: return 1.7
    if v > 0.0:  return 1.3
    return 1.0

def _gain_visibility(km: float | None, state: str | None) -> float:
    v = 99.0 if km is None else km
    if state == "fog": return 1.4
    if v < 2.0:       return 1.4
    if v < 5.0:       return 1.2
    return 1.0

def _gain_low_sun(elev: float) -> float:
    if elev < 5.0:  return 1.4
    if elev < 10.0: return 1.2
    return 1.0

def _circ_dist(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d

def _daypart_from_sun(elev: float, az: float | None, lat: float | None) -> str:
    if elev < -6.0:
        return "night"
    if -6.0 <= elev < 0.0:
        return "late_evening" if (az is not None and az >= 180.0) else "early_morning"

    if az is None:
        if elev < 8.0:   return "early_morning"
        if elev < 20.0:  return "morning"
        if elev < 35.0:  return "late_morning"
        if elev < 45.0:  return "midday"
        if elev < 20.0:  return "afternoon"
        if elev < 8.0:   return "late_afternoon"
        return "evening"

    mid_az = 180.0 if (lat is None or lat >= 0.0) else 0.0
    if elev >= 35.0 and _circ_dist(az, mid_az) <= 30.0:
        return "midday"

    if az < 180.0:
        if elev < 8.0:   return "early_morning"
        if elev < 20.0:  return "morning"
        if elev < 35.0:  return "late_morning"
        return "late_morning"
    else:
        if elev >= 35.0: return "afternoon"
        if elev >= 20.0: return "afternoon"
        if elev >= 8.0:  return "late_afternoon"
        return "evening"

def _localized_daypart(slug: str, lang: str) -> str:
    labels_en = {
        "night":"night", "late_evening":"late evening", "early_morning":"early morning",
        "morning":"forenoon", "late_morning":"late forenoon", "midday":"midday",
        "afternoon":"afternoon", "late_afternoon":"late afternoon", "evening":"evening"
    }
    labels_de = {
        "night":"Nacht", "late_evening":"Spätabend", "early_morning":"Früher Morgen",
        "morning":"Vormittag", "late_morning":"Später Vormittag", "midday":"Mittag",
        "afternoon":"Nachmittag", "late_afternoon":"Später Nachmittag", "evening":"Abends"
    }
    table = labels_de if (lang or "").lower().startswith("de") else labels_en
    return table.get(slug, slug)

# ---------------------------- Setup ---------------------------- #
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = {**entry.data, **entry.options}
    name = data.get(CONF_NAME, DEFAULT_NAME)

    entity = IlluminancePlus(hass, name, data, entry.entry_id)
    async_add_entities([entity], update_before_add=True)

    # Entity-Service 'refresh' registrieren
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "refresh",
        {},                       # keine Service-Parameter
        "async_force_refresh",    # Methodenname in der Entity (s. unten)
    )

# --------------------------- Entity --------------------------- #
class IlluminancePlus(SensorEntity):
    """Lux-Sensor mit wetterabhängiger Dämpfung + Attributen; is_dark basiert auf geglätteter Steuergröße."""

    _attr_device_class = "illuminance"
    _attr_state_class = "measurement"
    _attr_native_unit_of_measurement = UNIT_LUX
    _attr_attribution = "Illuminance Plus - © 2025 Martin Kluger · Clear-sky model by pnbruckner (ha-illuminance)"

    def __init__(self, hass: HomeAssistant, name: str, cfg: dict[str, Any], entry_id: str) -> None:
        self.hass = hass
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_lux"
        self.cfg = cfg

        # Hysterese & Glättung
        self._is_dark: bool | None = None
        self._ema: float | None = None  # geglättete Lux für Steuerung
        self._tau: float = float(cfg.get(CONF_SMOOTH_SECONDS, DEFAULT_SMOOTH_SECONDS))
        self._scan_secs: float = float(cfg.get(CONF_SCAN, DEFAULT_SCAN_SECONDS))

        # NEU: Lock für manuellen Refresh
        self._refresh_lock = asyncio.Lock()

        self._unsub = async_track_time_interval(
            hass, self._update, timedelta(seconds=int(self._scan_secs))
        )

    async def async_force_refresh(self) -> None:
        """Sofort neu berechnen (manuell), kurz & sicher."""
        async with self._refresh_lock:
            try:
                await self._update(None)
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Illuminance Plus: manual refresh failed: %s", err)
            finally:
                self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await self._update(None)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    def _smooth(self, raw: float) -> float:
        """Exponentiell gleitender Mittelwert (EMA) über 'tau' Sekunden."""
        if self._tau is None or self._tau <= 0:
            return raw
        # Alpha aus kontinuierlicher Zeitkonstante, bezogen auf Abtastzeit
        alpha = 1.0 - math.exp(-self._scan_secs / max(1.0, self._tau))
        if self._ema is None:
            self._ema = raw
        else:
            self._ema = (1.0 - alpha) * self._ema + alpha * raw
        return self._ema

    async def _update(self, _now) -> None:
        # Eingaben
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

        # Tagesabschnitt
        lat = getattr(self.hass.config, "latitude", None)
        daypart_en = _daypart_from_sun(elev, az, lat)
        lang = getattr(self.hass.config, "language", "en") or "en"
        daypart_label = _localized_daypart(daypart_en, lang)

        # Hysterese auf Basis der geglätteten Steuergröße
        on_thr  = float(self.cfg.get(CONF_ON, 1000))
        off_thr = float(self.cfg.get(CONF_OFF, 3000))

        # NEU: Empfindlichkeit nur für is_dark
        sens_pct = float(self.cfg.get(CONF_DARK_SENSITIVITY, DEFAULT_DARK_SENSITIVITY))
        sens = max(1e-6, sens_pct / 100.0)
        on_eff  = on_thr  * sens
        off_eff = off_thr * sens

        if self._is_dark is None:
            self._is_dark = (control_lux <= on_eff)
        else:
            if control_lux <= on_eff:
                self._is_dark = True
            elif control_lux >= off_eff:
                self._is_dark = False

        # Attribute
        self._attr_extra_state_attributes = {
            "daypart": daypart_en,
            "daypart_label": daypart_label,
            "is_dark": self._is_dark,
            "on_threshold": on_thr,
            "off_threshold": off_thr,
            # NEU: sichtbare effektive Schwellen & Empfindlichkeit
            "dark_sensitivity_pct": int(round(sens_pct)),
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
            "attribution": "Illuminance Plus © 2025 Martin Kluger · Clear-sky model by pnbruckner",
        }

        self.async_write_ha_state()
