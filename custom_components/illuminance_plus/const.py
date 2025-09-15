# Illuminance Plus – © 2025 Martin Kluger
# Based on clear-sky model by pnbruckner (ha-illuminance)
# License: MIT

DOMAIN = "illuminance_plus"

DEFAULT_NAME = "Illuminance Plus"
DEFAULT_MODE = "normal"  # normal | simple
DEFAULT_SCAN_SECONDS = 120
DEFAULT_FALLBACK = 10.0
DEFAULT_MAX_CLOUD_DIV = 10.0
DEFAULT_SMOOTH_SECONDS = 180  # Glättung für Steuerung (EMA), 0 = aus

# Optionen / Felder (bestehend)
CONF_NAME = "name"
CONF_MODE = "mode"
CONF_SCAN = "scan_seconds"
CONF_WEATHER = "weather_entity"      # weather.*
CONF_CLOUD = "cloud_entity"          # sensor 0–100 %
CONF_PRECIP = "precip_entity"        # sensor mm/h
CONF_VIS = "visibility_entity"       # sensor km
CONF_ON = "on_threshold"             # lx (Hysterese EIN)
CONF_OFF = "off_threshold"           # lx (Hysterese AUS)
CONF_MAX_CLOUD_DIV = "max_cloud_div" # max. Wolken-Dämpfung (÷)
CONF_SMOOTH_SECONDS = "smooth_seconds"

# Empfindlichkeit nur für is_dark (in %)
CONF_DARK_SENSITIVITY = "dark_sensitivity"
DEFAULT_DARK_SENSITIVITY = 100

# ----------------- NEU: Trend -----------------
CONF_TREND_ENABLED = "trend_enabled"
CONF_TREND_WIN_5M = "trend_window_5m"          # Minuten
CONF_TREND_WIN_15M = "trend_window_15m"        # Minuten
CONF_TREND_TH_DOWN = "darkening_fast_threshold" # lx/min (negativ)
CONF_TREND_TH_UP   = "brightening_fast_threshold" # lx/min (positiv)
DEFAULT_TREND_ENABLED = False
DEFAULT_TREND_WIN_5M = 5
DEFAULT_TREND_WIN_15M = 15
DEFAULT_TREND_TH_DOWN = -200.0
DEFAULT_TREND_TH_UP = 200.0

# ------------- NEU: Kurzfrist-Prognose -------------
CONF_FORECAST_ENABLED = "forecast_enabled"
CONF_FORECAST_15M = "forecast_15m"
CONF_FORECAST_30M = "forecast_30m"
CONF_FORECAST_60M = "forecast_60m"
CONF_DARK_SOON_MARGIN = "dark_soon_margin"     # lx Puffer zur EIN-Schwelle
DEFAULT_FORECAST_ENABLED = False
DEFAULT_FORECAST_15M = True
DEFAULT_FORECAST_30M = True
DEFAULT_FORECAST_60M = False
DEFAULT_DARK_SOON_MARGIN = 200.0

# ------------- NEU: Twilight-Flags -------------
CONF_TWILIGHT_ENABLED = "twilight_enabled"
DEFAULT_TWILIGHT_ENABLED = False

# ------------- NEU: Helper-Entitäten -------------
CONF_HELPERS_ENABLED = "helpers_enabled"
DEFAULT_HELPERS_ENABLED = False

# ------------- NEU: Fenster / Blendung -------------
CONF_WINDOWS_ENABLED = "windows_enabled"
CONF_WINDOWS_YAML = "windows_yaml"             # YAML-Liste (name, azimuth, fov, elev_min)
CONF_GLARE_ENABLED = "glare_enabled"
DEFAULT_WINDOWS_ENABLED = False
DEFAULT_WINDOWS_YAML = ""                       # leer = keine Fenster
DEFAULT_GLARE_ENABLED = True                    # wenn Fenster aktiv: Blend-Risiko berechnen

# Mapping, wenn KEIN numerischer Cloud-%-Sensor vorhanden
WEATHER_FACTORS = {
    "exceptional": 1.0, "sunny": 1.0, "clear": 1.0,
    "partlycloudy": 2.0, "cloudy": 5.0, "rainy": 5.0,
    "pouring": 10.0, "lightning": 10.0, "lightning-rainy": 10.0, "fog": 10.0,
}
