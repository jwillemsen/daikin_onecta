[![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86&style=for-the-badge)](https://github.com/sponsors/jwillemsen)
[![](https://img.shields.io/github/release/jwillemsen/daikin_onecta/all.svg?style=for-the-badge)](https://github.com/jwillemsen/daikin_onecta/releases)
[![](https://img.shields.io/badge/MAINTAINER-%40jwillemsen-green?style=for-the-badge)](https://github.com/jwillemsen)
[![](https://img.shields.io/codecov/c/github/jwillemsen/daikin_onecta?style=for-the-badge)](https://codecov.io/gh/jwillemsen/daikin_onecta)
# Daikin Onecta

Home Assistant Integration for Daikin devices using the Daikin Onecta API, requires Home Assistant 2024.1.0 as minimum HA version.

> [!IMPORTANT]
> Starting with v4.0.0 the cloud API has changed to the Daikin provided official API. In order to use this new API you need to create an account on the Daikin Developer Portal at https://developer.cloud.daikineurope.com/login. The status of the Daikin Cloud can be found online at https://daikincloudsolutions.statuspage.io.

> [!WARNING]
> Sharing, selling, or distribution access and refresh tokens is strictly prohibited according to the Daikin developer terms of use. Sharing them could case serious issues for you as user!

<!---
# Installation using HACS:

Install with [HACS](https://hacs.xyz): Search for "Daikin Onecta" in the default repository,
-->

# Installation

When using HACS add daikin_onecta as custom repository, select `HACS`, select `Integrations`, press the three dots in the upper right corner, select `Custom Repositories` and add https://github.com/jwillemsen/daikin_onecta as new repository. Now continue the installation as described at [Using config flow](https://github.com/jwillemsen/daikin_onecta/blob/master/readme.md#using-config-flow)

You can install the code manually by copying the `daikin_onecta` folder and all of its contents into your Home Assistant's `custom_components` folder. This is often located inside of your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the `custom_components` folder might be located at `/usr/share/hassio/homeassistant`. It is possible that your `custom_components` folder does not exist. If that is the case, create the folder in the proper location, and then copy the `daikin_onecta` folder and all of its contents inside the newly created `custom_components` folder. Then you have to restart Home Assistant for the component to be loaded properly.

# Prerequisites

Visit https://developer.cloud.daikineurope.com and sign up for a developer account. Enter the email of your login for the Onecta App from Daikin.

# Using config flow

First create an account at https://developer.cloud.daikineurope.com, after that create an application at the Daikin Developer website, see the Getting started page at the Daikin Developer portal for more information. As `redirect uri` you can use `https://my.home-assistant.io/redirect/oauth`. If you don’t have My Home Assistant on your installation, you can use `<HOME_ASSISTANT_URL>/auth/external/callback` as the redirect URI instead. The `<HOME_ASSISTANT_URL>` must be the same as used during the configuration/authentication process. Internal examples: `http://192.168.0.2:8123/auth/external/callback`, `http://homeassistant.local:8123/auth/external/callback`. Copy and save the provided client id and secret, you need to enter these in the next step.

Now within Home Assistant go to Settings - Devices & Services and pressing the `ADD INTEGRATION` button to create a new Integration, select `Daikin Onecta` in the drop-down menu. In the `Add credentials` form enter a user defined name (for example `daikin_onecta`), and enter the `OAuth Client ID` and `OAuth Client Secret` as you obtained from the Daikin website, and finish by pressing the 'ADD` button.

You will now be redirected to the Daikin website where you have to authorize the application. When you agree to give the application permissions you will be redirected back to the `redirect uri` as you provided as part of the application on the Daikin website, there you have to link Home Assisant by pressing the `Link account` button. In case the provided instance URL is not correct you can edit it by pressing the pencil behind the URL. When you have pressed `Link account` the integration will be added and th Daikin devices connected to your Daikin cloud account should now be visible within Home Assistant.

When you try to reinstall this integration check if you don't have an old client id and secret configured within Home Assistant, see [Application Credentials](https://www.home-assistant.io/integrations/application_credentials/) for more information.

This integration supports the following configuration settings to reduce the amount of polling to Daikin

- High frequency period update interval (minutes)
- Low frequency period update interval (minutes)
- High frequency period start time
- Low frequency period start time
- Number of seconds that a data refresh is ignored after a command

# Setting the log level

If you'd like to see more granular logs, to investigate the communication or for other debugging purposes, you can set the log level in the Home Assistant config. The following lines can be added to set the overall log level for the component and the oauth2 helper which this integration uses:

```
logger:
  logs:
    custom_components.daikin_onecta: debug
    homeassistant.helpers.config_entry_oauth2_flow: debug
```

If you only want to change log level on a per module basis, you can do that as well, for example if you only want debug logs for the climate:

```
logger:
  logs:
    custom_components.daikin_onecta.climate: debug
```

# Thanks to:

This code is based on [@rospogrigio](https://github.com/rospogrigio) and [@speleolontra](https://github.com/speleolontra) work which is based on [@Apollon77](https://github.com/Apollon77) work.
