# Illuminance Plus

Home Assistant Custom Integration. Modelliert die Außenhelligkeit (Lux) auf Basis Clear-Sky + Wetterdämpfung.
- UI-Setup & Re-Setup (Optionsflow)
- Glättung (EMA), Hysterese, Max. Wolken-Dämpfung
- Dayparts (DE/EN), `is_dark`, `control_lux` (geglättet)
- Entity-Service: `illuminance_plus.refresh`

## Installation (HACS, Custom Repo)
1. HACS → Integrationen → ⋮ → **Custom repositories** → URL dieses Repos, Kategorie **Integration**
2. Integration **Illuminance Plus** installieren, HA neu starten
3. Einstellungen → Geräte & Dienste → **Illuminance Plus** hinzufügen

## Optionen (Tuning)
- **Update (s):** 120–300
- **Glättung (s):** 180–240
- **Hysterese:** On 1000–1300 lx, Off 3000–3500 lx
- **Max. Cloud (÷):** 10–15

© 2025 Martin Kluger – Clear-sky model by pnbruckner (Credits).
