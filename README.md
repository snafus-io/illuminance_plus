# Illuminance Plus

> **DE & EN** – Deutsch zuerst, English version below.

---

## Inhaltsverzeichnis (DE)

- [Überblick](#überblick-de)
- [Hauptvorteile gegenüber pnbruckner](#hauptvorteile-gegenüber-pnbruckner-de)
- [Funktionsprinzip](#funktionsprinzip-de)
- [Installation](#installation-de)
  - [Über HACS (Custom Repository)](#über-hacs-custom-repository-de)
  - [Manuell (ohne HACS)](#manuell-ohne-hacs-de)
- [Einrichtung & Optionen](#einrichtung--optionen-de)
  - [Quellen](#quellen-de)
  - [Optionen erklärt](#optionen-erklärt-de)
- [Entität & Attribute](#entität--attribute-de)
- [Dienste](#dienste-de)
- [Best Practices & Tuning](#best-practices--tuning-de)
  - [Raumfaktor *k* (ohne zusätzliche Helfer)](#raumfaktor-k-ohne-zusätzliche-helfer-de)
  - [Hysterese richtig einstellen](#hysterese-richtig-einstellen-de)
  - [Empfohlene Startwerte](#empfohlene-startwerte-de)
- [Beispiele (Automationen, UI-kompatibel)](#beispiele-automattionen-ui-kompatibel-de)
  - [WC-Ecke (k = 1.4)](#wc-ecke-k--14-de)
  - [Bad (k = 1.3)](#bad-k--13-de)
  - [Küche (k = 1.2)](#küche-k--12-de)
- [Kompatibilität & Versionierung](#kompatibilität--versionierung-de)
- [Troubleshooting & FAQ](#troubleshooting--faq-de)
- [Credits & Lizenz](#credits--lizenz-de)

---

## Overview (EN)

- [Overview](#overview-en)
- [Key advantages over pnbruckner](#key-advantages-over-pnbruckner-en)
- [How it works](#how-it-works-en)
- [Installation](#installation-en)
  - [Via HACS (Custom Repository)](#via-hacs-custom-repository-en)
  - [Manual (without HACS)](#manual-without-hacs-en)
- [Setup & Options](#setup--options-en)
  - [Sources](#sources-en)
  - [Options explained](#options-explained-en)
- [Entity & Attributes](#entity--attributes-en)
- [Services](#services-en)
- [Best practices & tuning](#best-practices--tuning-en)
  - [Room factor *k* (no extra helpers)](#room-factor-k-no-extra-helpers-en)
  - [Set hysteresis properly](#set-hysteresis-properly-en)
  - [Recommended starting points](#recommended-starting-points-en)
- [Examples (Automations, UI-compatible)](#examples-automations-ui-compatible-en)
  - [WC corner (k = 1.4)](#wc-corner-k--14-en)
  - [Bathroom (k = 1.3)](#bathroom-k--13-en)
  - [Kitchen (k = 1.2)](#kitchen-k--12-en)
- [Compatibility & versioning](#compatibility--versioning-en)
- [Troubleshooting & FAQ](#troubleshooting--faq-en)
- [Credits & License](#credits--license-en)

---

## Überblick (DE)

**Illuminance Plus** modelliert die **Außenhelligkeit (Lux)** mit einer **Clear-Sky-Kurve** (nach *pnbruckner*) und dämpft diese mit **Wetterfaktoren** (Bewölkung, Niederschlag, Sichtweite). Ergebnis: **stabile, automationsfreundliche Werte** für die Innenraum-Lichtsteuerung – **ohne** echte Außen-Lichtsensoren.

- Robuste **Glättung (EMA)** + **Hysterese** gegen Flattern bei Wolken.
- **Dayparts** (Tagesabschnitte) aus Sonnenstand, **lokalisiert (DE/EN)**.
- **UI-Setup & Re-Konfiguration** (Options-Flow).
- **Entity-Dienst**: `illuminance_plus.refresh` für Sofort-Neuberechnung.

---

## Hauptvorteile gegenüber pnbruckner (DE)

- **UI-Optionen jederzeit änderbar** (kein Neu-Anlegen nötig).
- **Mehr Wetterquellen**: Cloud-%, Rain (mm/h), Visibility (km) – inkl. **Einheiten-Normalisierung**.
- **State vs. Steuergröße getrennt**:  
  State = `raw_lux` (ungeglättet, schön für Charts)  
  Attribut `control_lux` (geglättet) + `is_dark` (Hysterese) für Automationen.
- **Dayparts (DE/EN)**, genaue Abschnitte über Sonnengeometrie.
- **Refresh-Dienst** pro Entität.

---

## Funktionsprinzip (DE)

1. **Clear-Sky-Lux** (pnbruckner) aus **Sonnenhöhe**.
2. **Wetter-Dämpfung**: Cloud-Deckung, Niederschlag, Sichtweite → Faktoren/Divisoren.
3. **Rohwert `raw_lux`** = gedämpfte Clear-Sky-Helligkeit (Entitätszustand).
4. **Glättung (EMA)** → **`control_lux`** (Attribut): für Schaltschwellen & `is_dark`.
5. **Hysterese**: `on_threshold` / `off_threshold` auf **`control_lux`**.

---

## Installation (DE)

### Über HACS (Custom Repository) (DE)

1. **HACS → Integrationen → ⋮ → Custom repositories** → Repo-URL eintragen → **Integration** wählen.  
2. Integration installieren → **HA neu starten**.  
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Illuminance Plus“**.

### Manuell (ohne HACS) (DE)

1. Ordner `custom_components/illuminance_plus/` in dein HA `config/` kopieren.  
2. HA **neu starten** → Integration hinzufügen.

---

## Einrichtung & Optionen (DE)

### Quellen (DE)

- **Weather entity**: allgemeiner Wetterzustand (`sunny`, `cloudy`, `rainy`, `fog`, …) – *optional*, dient als Fallback für Dämpfung.
- **Cloud coverage**: **0–100 %** (idealerweise vom Wetterdienst) – wird in **Divisor** umgerechnet.
- **Precipitation**: **mm/h** (US-Einheiten werden automatisch in mm/h konvertiert).
- **Visibility**: **km** (US-Meilen werden automatisch nach km umgerechnet).

> Fehlende Quellen sind **optional** – die Integration fällt auf sinnvolle Defaults zurück.

### Optionen erklärt (DE)

- **Update (Sekunden)**: Berechnungsintervall. 120–300 s praxisgerecht.  
- **Glättung (Sek.)**: Zeitkonstante der EMA. 180–240 s = ruhig, aber reaktionsfähig.  
- **Hysterese**: On-/Off-Schwellen für **`control_lux`**. Typisch: **on 1000–1300**, **off 3000–3500**.  
- **Max. Wolken-Dämpfung (÷)**: Obergrenze der Cloud-Abdunkelung. Typisch **10–15**.

---

## Entität & Attribute (DE)

- **Zustand (`state`)**: `raw_lux` (ungeglättet, gerundet).  
- **Attribute (Auszug)**:
  - `control_lux` (geglättet, für Schaltlogik)  
  - `is_dark` (bool, basierend auf Hysterese)  
  - `on_threshold`, `off_threshold`  
  - `daypart`, `daypart_label` (EN/DE)  
  - Diagnose: `clear_sky_lux`, `cloud_divisor`, `rain_gain`, `visibility_gain`, `low_sun_gain`

---

## Dienste (DE)

- **`illuminance_plus.refresh`** (pro Entität): Sofort neu berechnen (unabhängig vom Updateintervall).  
  *Optional*: Ein globaler `refresh_all` kann in der Integration ergänzt werden.

---

## Best Practices & Tuning (DE)

### Raumfaktor *k* (ohne zusätzliche Helfer) (DE)

Pro Raum eigener „Helligkeits-Charakter“ via **Faktor `k`** (nur im Automations-Template).  
Vergleich jeweils gegen **effektive** Schwellen:

- **EIN**: `control_lux <= on_threshold * k`  
- **AUS**: `control_lux >= off_threshold * k`

**Typische Werte**:  
- dunkle Nische: **1.3–1.6**  
- normal: **1.0–1.2**  
- sehr hell: **0.8–0.9**

**`k` herleiten (ohne Helfer):**
- In dem Moment, wo du **„jetzt an“** willst: `k_on = control_lux / on_threshold`  
- In dem Moment, wo du **„jetzt aus“** willst: `k_off = control_lux / off_threshold`  
- **k ≈ (k_on + k_off) / 2**

### Hysterese richtig einstellen (DE)

- Baseline-Raum wählen (z. B. normal hell).  
- Bei **„jetzt an“**: `on_threshold ≈ L_on / k_baseline`  
- Bei **„jetzt aus“**: `off_threshold ≈ L_off / k_baseline`  
- Global stabil lassen, pro Raum nur **k** feinjustieren (±0.1).

### Empfohlene Startwerte (DE)

- **Update**: 120–300 s  
- **Glättung**: 180–240 s  
- **Hysterese**: on 1000–1300, off 3000–3500  
- **Cloud ÷**: 10–15

---

## Beispiele (Automattionen, UI-kompatibel) (DE)

> Passe nur Entitäts-IDs & `k` an. Die Hysterese bleibt global in der Integration definiert.

### WC-Ecke (k = 1.4) (DE)

```yaml
alias: Licht WC-Ecke (Illuminance Plus)
mode: restart
triggers:
  - platform: state
    entity_id: binary_sensor.bad_wc_presence_sensor
    to: "on"
  - platform: state
    entity_id: binary_sensor.bad_wc_presence_sensor
    to: "off"
  - platform: state
    entity_id: sensor.illuminance_plus
conditions: []
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: binary_sensor.bad_wc_presence_sensor
            state: "on"
          - condition: state
            entity_id: light.wc_ecke
            state: "off"
          - condition: template
            value_template: >
              {% set lux = state_attr('sensor.illuminance_plus','control_lux')|float(0) %}
              {% set onb = state_attr('sensor.illuminance_plus','on_threshold')|float(1200) %}
              {% set k = 1.4 %}
              {{ lux <= onb * k }}
        sequence:
          - service: light.turn_on
            target: { entity_id: light.wc_ecke }
      - conditions:
          - condition: state
            entity_id: binary_sensor.bad_wc_presence_sensor
            state: "on"
          - condition: state
            entity_id: light.wc_ecke
            state: "on"
          - condition: template
            value_template: >
              {% set lux = state_attr('sensor.illuminance_plus','control_lux')|float(0) %}
              {% set offb = state_attr('sensor.illuminance_plus','off_threshold')|float(3200) %}
              {% set k = 1.4 %}
              {{ lux >= offb * k }}
        sequence:
          - service: light.turn_off
            target: { entity_id: light.wc_ecke }
```

### Bad (k = 1.3) (DE)

```yaml
# identisch, nur k = 1.3 und Entity-IDs für Bad anpassen
```

### Küche (k = 1.2) (DE)

```yaml
# identisch, nur k = 1.2 und Entity-IDs für Küche anpassen
```

---

## Kompatibilität & Versionierung (DE)

- Getestet mit **Home Assistant ≥ 2024.6**.  
- Nutzt **stabile öffentliche APIs** (SensorEntity, entity services, sun.sun).  
- Lux-Einheit **versionssicher** (Fallback auf ältere Konstanten).

---

## Troubleshooting & FAQ (DE)

- **Dienst fehlt?** → `services.yaml` unter `custom_components/illuminance_plus/` vorhanden? In `sensor.py` `entity_platform.async_register_entity_service(...)` aufgerufen? HA neu starten.  
- **Quellen fehlen?** → Optional; die Integration hat Fallbacks. Bessere Daten = realistischere Lux.  
- **Flattert bei Wolken?** → Glättung erhöhen (z. B. 240 s) und genügend Abstand zwischen on/off lassen.  
- **Re-Setup?** → In der Integrationskachel **⋮ → Optionen**.

---

## Credits & Lizenz (DE)

- Clear-Sky-Modell: **pnbruckner** (ha-illuminance).  
- Entwicklung & Erweiterung: **Martin Kluger**.  
- Lizenz: **MIT**.

---

# Overview (EN)

**Illuminance Plus** models **outdoor illuminance (Lux)** with a **clear-sky curve** (by *pnbruckner*), attenuated by **weather inputs** (cloud cover, precipitation, visibility). It yields **stable, automation-ready values** for indoor lighting – **without** physical outdoor sensors.

---

## Key advantages over pnbruckner (EN)

- **UI options** can be adjusted anytime (no delete/re-add).  
- **More weather inputs**: cloud %, rain (mm/h), visibility (km) – with **unit normalization**.  
- **State vs control value** separated (charts vs switching).  
- **Dayparts** with **EN/DE** labels.  
- **Per-entity refresh service**.

---

## How it works (EN)

1. **Clear-sky lux** from **solar elevation**.  
2. **Weather attenuation** via cloud/rain/visibility.  
3. **`raw_lux`** (entity state).  
4. **EMA smoothing** → **`control_lux`** (attribute).  
5. **Hysteresis** (`on_threshold`/`off_threshold`) on `control_lux`.

---

## Installation (EN)

### Via HACS (Custom Repository) (EN)

1. **HACS → Integrations → ⋮ → Custom repositories** → add this repo as **Integration**.  
2. Install → **restart HA**.  
3. **Settings → Devices & Services → Add Integration → “Illuminance Plus”**.

### Manual (without HACS) (EN)

1. Copy `custom_components/illuminance_plus/` into your HA `config/`.  
2. **Restart** HA → add the integration.

---

## Setup & Options (EN)

### Sources (EN)

- **Weather entity** (state string): general weather (`sunny`, `cloudy`, `rainy`, `fog`, …).  
- **Cloud coverage**: **0–100 %**.  
- **Precipitation**: **mm/h** (US units converted to mm/h).  
- **Visibility**: **km** (miles converted to km).

### Options explained (EN)

- **Update (seconds)**: recompute interval (120–300 s recommended).  
- **Smoothing (seconds)**: EMA time constant (180–240 s recommended).  
- **Hysteresis**: on/off thresholds for **`control_lux`** (1000–1300 / 3000–3500 typical).  
- **Max cloud attenuation (÷)**: upper bound for cloud attenuation (10–15 typical).

---

## Entity & Attributes (EN)

- **State**: `raw_lux` (unsmoothed).  
- **Attributes**: `control_lux`, `is_dark`, `on_threshold`, `off_threshold`, `daypart`, `daypart_label`, diagnostics (`clear_sky_lux`, `cloud_divisor`, etc.).

---

## Services (EN)

- **`illuminance_plus.refresh`** (per entity): trigger instant recalculation.  
  *Optional*: `refresh_all` if you added a global service.

---

## Best practices & tuning (EN)

### Room factor *k* (no extra helpers) (EN)

- **ON**: `control_lux <= on_threshold * k`  
- **OFF**: `control_lux >= off_threshold * k`

Typical `k`: dark 1.3–1.6, normal 1.0–1.2, very bright 0.8–0.9.  
Derive `k`: measure `control_lux` at your subjective ON/OFF moments →  
`k_on = control_lux / on_threshold`, `k_off = control_lux / off_threshold`, `k ≈ (k_on + k_off)/2`.

### Set hysteresis properly (EN)

Choose a baseline room, measure `L_on`/`L_off`, compute:  
`on_threshold ≈ L_on / k_baseline`, `off_threshold ≈ L_off / k_baseline`.  
Then fine-tune per-room `k` (±0.1).

### Recommended starting points (EN)

- Update 120–300 s, Smoothing 180–240 s, Hysteresis on 1000–1300 / off 3000–3500, Cloud ÷ 10–15.

---

## Examples (Automations, UI-compatible) (EN)

> Same as German examples; only change entity IDs and `k` per room. (See above.)

---

## Compatibility & versioning (EN)

- Tested with **Home Assistant ≥ 2024.6**.  
- Uses **stable public APIs** only.  
- Lux unit is **backwards-compatible** (fallbacks).

---

## Troubleshooting & FAQ (EN)

- **Service missing?** Check `services.yaml` and registration in `sensor.py`; restart HA.  
- **Missing sources?** They’re optional; better data → better lux.  
- **Flicker under clouds?** Increase smoothing and keep a healthy gap between on/off.  
- **Re-setup?** Use the integration’s **Options** menu.

---

## Credits & License (EN)

- Clear-sky model: **pnbruckner** (ha-illuminance).  
- Development & extensions: **Martin Kluger**.  
- License: **MIT**.
