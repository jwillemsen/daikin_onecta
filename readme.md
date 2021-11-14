# Daikin Residential for Altherma 3

This work is inspired from Rospogrigio "daikin_residential" repository (https://github.com/rospogrigio/daikin_residential) and modified to support Daikin Altherma 3 Heat Pump.

# Installation:

Copy the daikin_residential folder and all of its contents into your Home Assistant's custom_components folder. This is often located inside of your /config folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the custom_components folder might be located at /usr/share/hassio/homeassistant. It is possible that your custom_components folder does not exist. If that is the case, create the folder in the proper location, and then copy the daikin_residential folder and all of its contents inside the newly created custom_components folder.

# YAML config files

Just add the following lines to your configuration.yaml file specifying the email and password used in the Daikin Residential App, and the Daikin devices connected to your cloud account will be created.


daikin_residential_altherma:
  email: [your_email]
  password: [your_pwd]



# Thanks to:

This code is based on @Rospogrigio's work that in turn is based on @Apollon77 's work, in finding a way to retrieve the token set, and to send the HTTP commands over the cloud. This integration would not exist without their precious job, my job was to try and debug Rospogrigio's code to adapt at JSON from Altherma 3 controlled by Daikin Residential App.
