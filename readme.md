[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Daikin Residential for Altherma 3 Heat Pump

Home Assistant Integration for Daikin Altherma 3 Heat Pump. This integration can coexist with the [daiking_residential integration](https://github.com/rospogrigio/daikin_residential).

This integration is maintained by [@speleolontra](https://github.com/speleolontra) and [@jwillemsen](https://github.com/jwillemsen).

# Installation using HACS:

Install with [HACS](https://hacs.xyz): Search for "Daikin Residential for Altherma 3" in the default repository,

# Manual Installation

Copy the `daikin_residential_altherma` folder and all of its contents into your Home Assistant's `custom_components` folder. This is often located inside of your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the `custom_components` folder might be located at `/usr/share/hassio/homeassistant`. It is possible that your `custom_components` folder does not exist. If that is the case, create the folder in the proper location, and then copy the `daikin_residential_altherma` folder and all of its contents inside the newly created `custom_components` folder. Then you have to restart Home Assistant for the component to be loaded properly.

# Using config flow

Start by going to Configuration - Integration and pressing the `+ ADD INTEGRATION` button to create a new Integration, then select `Daikin Residential Controller for Altherma` in the drop-down menu.

Follow the instructions, you just have to type the email and password used in the Daikin Residential App. After pressing the "Submit" button, the integration will be added, and the Daikin devices connected to your cloud account will be created.

# YAML config files

Just add the following lines to your `configuration.yaml` file specifying the email and password used in the Daikin Residential App, and the Daikin devices connected to your cloud account will be created. After making changes to your `configuration.yaml` file you need to restart home assistant.

```
daikin_residential_altherma:
  email: [your_email]
  password: [your_pwd]
```

# Setting the log level

If you'd like to see more granular logs, to investigate the communication or for other debugging purposes, you can set the log level in the Home Assistant config. The following lines can be added to set the overall log level for the component:

```
logger:
  logs:
    custom_components.daikin_residential_altherma: debug
```

If you only want to change log level on a per module basis, you can do that as well, for example if you only want debug logs for the climate:

```
logger:
  logs:
    custom_components.daikin_residential_altherma.climate: debug
```

# Thanks to:

This code is based on [@rospogrigio](https://github.com/rospogrigio) work that in turn is based on [@Apollon77](https://github.com/Apollon77) work, in finding a way to retrieve the token set, and to send the HTTP commands over the cloud. This integration would not exist without their precious job, my job was to try and debug Rospogrigio's code to adapt at JSON from Altherma 3 controlled by Daikin Residential App.

# Next steps

- Simplify integration by grouping all sensors in their management point, there is a lot of code duplication and special handling for the Altherma water tank in the current code which we want to simplify
