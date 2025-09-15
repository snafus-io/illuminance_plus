# Illuminance Plus – © 2025 Martin Kluger
# Based on clear-sky model by pnbruckner (ha-illuminance)
# License: MIT

DOMAIN = "illuminance_plus"

DEFAULT_NAME = "Illuminance Plus"
DEFAULT_MODE = "normal"  # normal | simple  (pnb ist Standard im 'normal')
DEFAULT_SCAN_SECONDS = 120
DEFAULT_FALLBACK = 10.0
DEFAULT_MAX_CLOUD_DIV = 10.0
DEFAULT_SMOOTH_SECONDS = 180  # Glättung für Steuerung (EMA), 0 = aus

# Optionen / Felder
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

# NEU: Empfindlichkeit nur für is_dark (in %)
CONF_DARK_SENSITIVITY = "dark_sensitivity"
DEFAULT_DARK_SENSITIVITY = 100

# Mapping, wenn KEIN numerischer Cloud-%-Sensor vorhanden
WEATHER_FACTORS = {
    "exceptional": 1.0, "sunny": 1.0, "clear": 1.0,
    "partlycloudy": 2.0, "cloudy": 5.0, "rainy": 5.0,
    "pouring": 10.0, "lightning": 10.0, "lightning-rainy": 10.0, "fog": 10.0,
}
