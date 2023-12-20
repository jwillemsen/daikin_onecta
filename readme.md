[![](https://img.shields.io/github/release/jwillemsen/daikin_residential_altherma/all.svg?style=for-the-badge)](https://github.com/jwillemsen/daikin_residential_altherma/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/badge/MAINTAINER-%40jwillemsen-green?style=for-the-badge)](https://github.com/jwillemsen)


# Daikin Residential including Altherma 3 Heat Pump

Home Assistant Integration for Daikin devices including Daikin Altherma 3 Heat Pump.

This integration is maintained by [@jwillemsen](https://github.com/jwillemsen).

> [!IMPORTANT]
> Starting with v3.0.0 the internal IDs of all entities have changed, please check your automations and energy dashboard whether you need to update these.

<!---
# Installation using HACS:

Install with [HACS](https://hacs.xyz): Search for "Daikin Residential for Altherma 3" in the default repository,
-->

# Manual Installation

Copy the `daikin_residential_altherma` folder and all of its contents into your Home Assistant's `custom_components` folder. This is often located inside of your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the `custom_components` folder might be located at `/usr/share/hassio/homeassistant`. It is possible that your `custom_components` folder does not exist. If that is the case, create the folder in the proper location, and then copy the `daikin_residential_altherma` folder and all of its contents inside the newly created `custom_components` folder. Then you have to restart Home Assistant for the component to be loaded properly.

# Using config flow

Start by going to Configuration - Integration and pressing the `+ ADD INTEGRATION` button to create a new Integration, then select `Daikin Residential Controller for Altherma` in the drop-down menu.

Follow the instructions, you just have to type the email and password used in the Daikin Residential App. After pressing the "Submit" button, the integration will be added, and the Daikin devices connected to your cloud account will be created.

# YAML config files

Just add the following lines to your `configuration.yaml` file specifying the email and password used in the Daikin Residential App, and the Daikin devices connected to your cloud account will be created. After making changes to your `configuration.yaml` file you need to restart home assistant.

```
daikin_residential_altherma:
  email: 'your_email'
  password: 'your_pwd'
```

# Known Issues and troubleshooting

- I am getting the following error when adding the integration: **Failed to retrieve Access Token: ('Login failed: %s', Exception('Unknown Login error: Login Failed Captcha Required'))**

**Solution:** when you have logged in to Daikin services, you have probably used the "Login with Google account" or other service. Try registering on Daikin platform, or register another account and share the devices with that account, then use that second account to configure this Integration.

- I am getting the following error when adding the integration: **Failed to retrieve Access Token: ('Failed to retrieve access token: %s', IATError('Issued in the future'))**

**Solution:** probably your system time is too out of sync with the token issuer's one. Make sure your system datetime is up-to-date, and in general it is advised to connect to an NTP server to keep your datetime synced.

- I am having other general network problems that don't allow me to get or update the connection token

**Solution:** make sure you don't have issues connecting to the address `daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com` or similar. In general, check if you have any web filtering or adblocking system that might interfere with these connections: try to disable them, and if it starts working then try whitelisting this address or similar. Check if you have ipv6 enabled, some users report problems when using ipv6, try to disable ipv6.


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
