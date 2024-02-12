#!/usr/bin/python3
#

import datetime
import asyncio
import sys
import json
import requests
import logging

logging.basicConfig() 
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(level=logging.DEBUG)  # Debug hack!


class DaikinCloudController():
    """Daikin Cloud Controller."""

    def __init__(self):
        """Initialize a new Daikin Cloud Controller."""
        tokenFile = 'tokenset.json';
        self.tokenSet = None
        with open(tokenFile) as jsonFile:
            jsonObject = json.load(jsonFile)            
            self.tokenSet = jsonObject
            jsonFile.close()

        configuration = {
            'issuer': 'https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_SLI9qJpc7',
            'authorization_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/authorize',
            'userinfo_endpoint': 'userinfo_endpoint',
            'token_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/token',
            'token_endpoint_auth_methods_supported': ['none']
        }
        _LOGGER.info("Initialized Daikin Cloud Controller")
        _LOGGER.debug("Daikin Cloud Controller token is [%s]",self.tokenSet['access_token'])


    async def doBearerRequest(self, resourceUrl, options=None, refreshed=False):
        if self.tokenSet == None:
            raise Exception('Please provide a TokenSet or use the Proxy server to Authenticate once')

        if not resourceUrl.startswith('http'):
            resourceUrl = 'https://api.prod.unicloud.edc.dknadmin.be' + resourceUrl

        headers = {
            'user-agent': 'Daikin/1.6.1.4681 CFNetwork/1209 Darwin/20.2.0',
            'x-api-key': 'xw6gvOtBHq5b1pyceadRp6rujSNSZdjx2AqT03iC', 
            'Authorization': 'Bearer ' + self.tokenSet["access_token"],
            'Content-Type': 'application/json'
        }


        _LOGGER.debug('BEARER REQUEST URL: %s', resourceUrl)
        _LOGGER.debug("BEARER REQUEST HEADERS: %s",headers)
        if options != None and 'method' in options and options['method'] == 'PATCH':
            _LOGGER.debug("BEARER REQUEST JSON: %s",options['json'])
            res = requests.patch(resourceUrl, headers=headers, data=options['json'])
        else:
            res = requests.get(resourceUrl, headers=headers)
        _LOGGER.debug("BEARER RESPONSE CODE: %s",res.status_code)

        if res.status_code == 200:
            try:
                return res.json()
            except:
                return res.text
        if res.status_code == 204:
            return True
        
        if not refreshed and res.status_code == 401:
            _LOGGER.info("TOKEN EXPIRED: will refresh it (%s)",res.status_code)
            await self.refreshAccessToken()
            return await self.doBearerRequest(resourceUrl, options,True)

        raise Exception('Communication failed! Status: ' + str(res.status_code))


    async def refreshAccessToken(self):
        """Attempt to refresh the Access Token."""
        url = 'https://cognito-idp.eu-west-1.amazonaws.com'
        
        headers = {
            'Content-Type': 'application/x-amz-json-1.1',
            'x-amz-target': 'AWSCognitoIdentityProviderService.InitiateAuth',
            'x-amz-user-agent': 'aws-amplify/0.1.x react-native',
            'User-Agent': 'Daikin/1.6.1.4681 CFNetwork/1220.1 Darwin/20.3.0'
        }
        ref_json= {
            'ClientId': '7rk39602f0ds8lk0h076vvijnb',
            'AuthFlow': 'REFRESH_TOKEN_AUTH',
            'AuthParameters': {
                'REFRESH_TOKEN': self.tokenSet["refresh_token"]
            }
        }
        res = requests.post(url, headers=headers, json=ref_json)
        _LOGGER.info("REFRESHACCESSTOKEN RESPONSE CODE: %s",res.status_code)
        _LOGGER.debug("REFRESHACCESSTOKEN RESPONSE: %s",res.json())
        res_json = res.json()
        if res.status_code != 200:
            raise Exception('Token refresh was not successful! Status: ' + str(res.status_code))

        if res_json['AuthenticationResult'] != None and res_json['AuthenticationResult']['AccessToken'] != None and res_json['AuthenticationResult']['TokenType'] == 'Bearer':
            self.tokenSet['access_token'] = res_json['AuthenticationResult']['AccessToken']
            self.tokenSet['id_token'] = res_json['AuthenticationResult']['IdToken']
            self.tokenSet['expires_at'] = int(datetime.datetime.now().timestamp()) + int(res_json['AuthenticationResult']['ExpiresIn'])
            _LOGGER.debug("NEW TOKENSET: %s",self.tokenSet)
            with open('tokenset.json', 'w') as outfile:
                json.dump(self.tokenSet, outfile)

            return self.tokenSet;
        raise Exception('Token refresh was not successful! Status: ' + str(res.status_code))


    async def getApiInfo(self):
        """Get Daikin API Info."""
        return await self.doBearerRequest('/v1/info')


    async def getCloudDeviceDetails(self):
        """Get pure Device Data from the Daikin cloud devices."""
        return await self.doBearerRequest('/v1/gateway-devices')

    async def getCloudDeviceData(self, devId):
        """Get pure Device Data of a single Daikin cloud device."""
        return await self.doBearerRequest('/v1/gateway-devices/' + devId)


async def main():
	
	controller = DaikinCloudController()
	resp = await controller.getApiInfo()
	_LOGGER.info("\nAPI INFO: %s\n",resp)
	resp = await controller.getCloudDeviceDetails()
	with open("daikin_data.json", 'w') as jsonFile:
		_LOGGER.info("Dumping json file daikin_data.json\n")
		json.dump(resp, jsonFile, indent=4, sort_keys=True)

asyncio.run(main())


print ("END")

sys.exit(0)

