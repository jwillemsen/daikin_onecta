# Daikin Residential for Altherma 3

This work is inspired from Rospogrigio [daikin_residential](https://github.com/rospogrigio/daikin_residential) integration and modified to support Daikin Altherma 3 Heat Pump. For a Altherma 3 using a BRP069A61 or BRP069A62 adapter you can use the [daikin_residential_brp069a62](https://github.com/BigFoot2020/daikin_residential_brp069a62) integration.

# WARNING
This is an experimental integration, tested on some Daikin Altherma 3 (BRP069A78) units.
The HA Integration was cloned by Rospogrigio's work and can coexisting with the daiking_residential integration.

# Installation using HACS:

Open "HACS" section then "Integrations" and click on three points menu at top right. Click on "custom reporitories" and add "https://github.com/speleolontra/daikin_residential_altherma" as integration category.
this will copy the "daikin_residential_altherma" folder in the "custom_components" folder of Home Assistant.
Make sure to restart home Assistant, then go to "Using config flow" chapter.

# Manual Installation

Copy the "daikin_residential_altherma" folder and all of its contents into your Home Assistant's "custom_components" folder. This is often located inside of your "/config" folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the "custom_components" folder might be located at "/usr/share/hassio/homeassistant". It is possible that your "custom_components" folder does not exist. If that is the case, create the folder in the proper location, and then copy the "daikin_residential_altherma" folder and all of its contents inside the newly created "custom_components" folder.

# Using config flow

Start by going to Configuration - Integration and pressing the "+ ADD INTEGRATION" button to create a new Integration, then select Daikin Residential Controller in the drop-down menu.

Follow the instructions, you just have to type the email and password used in the Daikin Residential App. After pressing the "Submit" button, the integration will be added, and the Daikin devices connected to your cloud account will be created.

# YAML config files (not tested)

Just add the following lines to your configuration.yaml file specifying the email and password used in the Daikin Residential App, and the Daikin devices connected to your cloud account will be created.

```
daikin_residential_altherma:
  email: [your_email]
  password: [your_pwd]
```

# Thanks to:

This code is based on @Rospogrigio's work that in turn is based on @Apollon77 's work, in finding a way to retrieve the token set, and to send the HTTP commands over the cloud. This integration would not exist without their precious job, my job was to try and debug Rospogrigio's code to adapt at JSON from Altherma 3 controlled by Daikin Residential App.

# Next steps

- Better support of the hot water tank entity
- Other ideas?
