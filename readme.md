[![](https://img.shields.io/github/release/jwillemsen/daikin_residential_altherma/all.svg?style=for-the-badge)](https://github.com/jwillemsen/daikin_residential_altherma/releases)
<!---
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
-->
[![](https://img.shields.io/badge/MAINTAINER-%40jwillemsen-green?style=for-the-badge)](https://github.com/jwillemsen)


# Daikin Residential including Altherma 3 Heat Pump

Home Assistant Integration for Daikin devices including Daikin Altherma 3 Heat Pump.

> [!IMPORTANT]
> Starting with v3.0.0 the internal IDs of all entities have changed, please check your automations and energy dashboard whether you need to update these. When you remove the other Daikin integrations from your HA installation the history from those will be lost.

<!---
# Installation using HACS:

Install with [HACS](https://hacs.xyz): Search for "Daikin Residential for Altherma 3" in the default repository,
-->

# Manual Installation

Copy the `daikin_residential_altherma` folder and all of its contents into your Home Assistant's `custom_components` folder. This is often located inside of your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the `custom_components` folder might be located at `/usr/share/hassio/homeassistant`. It is possible that your `custom_components` folder does not exist. If that is the case, create the folder in the proper location, and then copy the `daikin_residential_altherma` folder and all of its contents inside the newly created `custom_components` folder. Then you have to restart Home Assistant for the component to be loaded properly.

# Using config flow

Start by going to Settings - Devices & Services and pressing the `+ ADD INTEGRATION` button to create a new Integration, then select `Daikin Residential Controller including Altherma 3` in the drop-down menu.

Follow the instructions, you have to login at Daikin and authorize the application. After pressing the "Submit" button, the integration will be added, and the Daikin devices connected to your cloud account will be created.

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

This code is based on [@rospogrigio](https://github.com/rospogrigio) and [@speleolontra](https://github.com/speleolontra) work which is based on [@Apollon77](https://github.com/Apollon77) work.
