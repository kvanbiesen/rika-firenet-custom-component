# Rika Firenet (forked from Fockaert/rika-firenet-custom-component)

_Component to integrate with Rika Firenet [rikafirenet]._

**This component will set up the following platforms.**

Platform | Description
-- | --
`climate` | ...
`sensor` | ...

## Installation

HACS or:

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `rika_firenet`.
4. Download _all_ the files from the `custom_components/rika_firenet/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Rika Firenet"

## Configuration is done in the UI

## Lovelace: 

![alt text](https://raw.githubusercontent.com/antibill51/rika-firenet-custom-component/main/Screenshot/capture.png)

### Cards :

custom:config-template-card
custom:stack-in-card
custom:bar-card
custom:mini-graph-card
custom:simple-thermostat

Pellet in stock, tank level.
I use GSG2.0 for Pellet stock. https://domotique-home.fr/gestion-de-chauffage-stock-de-granules-gsg/

### Informations: 

I bypass Rika built'in thermostat with PID Thermostat.

Examples in HA config folder. (lovelace / automations / ...)

rika_domo: name of the stove from this component. Replace with your.
climate.rika: PID thermostat using https://github.com/antibill51/HASmartThermostat (fork of https://github.com/ScratMan/HASmartThermostat with toggle_header for hvac_action with pwm: 0 ).
climate.rika_z2: PID thermostat.

If I forgot elements, ask for it ;)


## Utility meters example: (I don't use it)
```yaml
utility_meter:
  hourly_stove_consumption:
    source: sensor.<stove>_stove_consumption
    cycle: hourly
  daily_stove_consumption:
    source: sensor.<stove>_stove_consumption
    cycle: daily
  weekly_stove_consumption:
    source: sensor.<stove>_stove_consumption
    cycle: weekly
  monthly_stove_consumption:
    source: sensor.<stove>_stove_consumption
    cycle: monthly

  hourly_stove_runtime:
    source: sensor.<stove>_stove_runtime
    cycle: hourly
  daily_stove_runtime:
    source: sensor.<stove>_stove_runtime
    cycle: daily
  weekly_stove_runtime:
    source: sensor.<stove>_stove_runtime
    cycle: weekly
  monthly_stove_runtime:
    source: sensor.<stove>_stove_runtime
    cycle: monthly
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[rikafirenet]: https://github.com/antibill51/rika-firenet-custom-component
[forum]: https://community.home-assistant.io/
[releases]: https://github.com/antibill51/rika-firenet-custom-component/releases
