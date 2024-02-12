#!/usr/bin/python3

import asyncio
import base64
import datetime
import json
import logging
import os
import re
import requests
import sys
import time
from time import sleep
from oic.oic import Client
from urllib import parse

# from daikin_device import DaikinCloudDevice

_LOGGER = logging.getLogger(__name__)
logging.basicConfig()  # TODO include function name/line numbers in _LOGGER
# _LOGGER.setLevel(logging.DEBUG)  # Debug hack!

class DaikinCloudController():
    """Daikin Cloud Controller."""

    def __init__(self):
        """Initialize a new Daikin Cloud Controller."""
        self.tokenSet = None

        self.name = "OK"
        configuration = {
            'issuer': 'https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_SLI9qJpc7',
            'authorization_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/authorize',
            'userinfo_endpoint': 'userinfo_endpoint',
            'token_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/token',
            'token_endpoint_auth_methods_supported': ['none']
        }

        self.openIdClientId = '7rk39602f0ds8lk0h076vvijnb'
        self.openIdClient = Client(client_id = self.openIdClientId, config=configuration)
        self.openIdClient.provider_config(configuration['issuer'])
        self.openIdStore = {}

        _LOGGER.info("Initialized Daikin Cloud Controller")


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

#            self.emit('token_update', self.tokenSet);
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

    async def getCloudDevices(self):
        """Get array of DaikinCloudDevice objects to interact with the device and get data."""
        devices = await self.getCloudDeviceDetails()
        res = [
            DaikinCloudDevice(dev, self)
            for dev in devices or []
        ]
        return res
        #res.update(dev)

    async def _doAuthorizationRequest(self):
        args = {"response_type": ["code"], "scope": "openid"}
        state = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').replace('=','')
        print("STATE: {}".format(state))
        args = {
            'authorization_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/authorize',
            'userinfo_endpoint': 'userinfo_endpoint',
            'response_type': ['code'],
            'scopes': 'email,openid,profile',
        }

        self.openIdClient.redirect_uris = ['daikinunified://login']
        _args, code_verifier = self.openIdClient.add_code_challenge()
        args.update(_args)
        self.openIdStore[state] = { 'code_verifier': code_verifier }

        auth_resp = self.openIdClient.do_authorization_request(request_args=args, state=state)
        self.state = state
        return auth_resp


    async def _doAccessTokenRequest(self, callbackUrl):
        # print('_RETRIEVETOKENS: '+ callbackUrl)
        params = dict(parse.parse_qsl(parse.urlsplit(callbackUrl).query))
        print('VERIFIER: '+ self.openIdStore[params['state']]['code_verifier'])
        state = self.state

        args = {
            'authorization_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/authorize',
            'token_endpoint': 'https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/oauth2/token',
            'token_endpoint_auth_methods_supported': ['none'],
            # 'userinfo_endpoint': 'userinfo_endpoint',
            'response_type': ['code'],
            'scopes': 'email,openid,profile',
            'state': state,
            'token_endpoint_auth_method': 'none' # (default 'client_secret_basic')
        }

        if self.openIdStore[state] is None:
             raise Exception('Can not decode response for State ' + state + '. Please reload start page and try again!')

        if params['code'] is not None:
            callbackParams = {
                'code_verifier': self.openIdStore[state]['code_verifier'],
                'state': state
            }
            # print('CB PARAMS: {}'.format(callbackParams))
            # print('PROVIDER_INFO: {}'.format(self.openIdClient.provider_info))
            rtk_resp = self.openIdClient.do_access_token_request(request_args=args, extra_args=callbackParams, state=state, authn_method=None)
            # print('_RETRIEVETOKENS RESP: {}'.format(rtk_resp))
            new_tokenset = {
                "access_token": rtk_resp["access_token"],
                "refresh_token": rtk_resp["refresh_token"],
                "expires_in": rtk_resp["expires_in"],
                "token_type": rtk_resp["token_type"]
            }
            print('NEW TOKENSET: {}'.format(new_tokenset))
            return new_tokenset
        else:
            raise Exception('Daikin-Cloud: ERROR.')

    async def retrieveAccessToken(self, userName, password):

        # Extract csrf state cookies
        try:
            response = await self._doAuthorizationRequest()
            cookies = response.headers['set-cookie']
            # print('COOKIES: ' + cookies)
            csrfStateCookie = ''
            for cookie in cookies.split(', '):
                for field in cookie.split(';'):
                    if 'csrf-state' in field:
                        if csrfStateCookie != '':
                            csrfStateCookie += "; "
                        csrfStateCookie += field.strip()

            # print('CSRFSTATECOOKIE COOKIES: {}'.format(csrfStateCookie))
            location = response.headers['location']
            # print('LOCATION: ' + location)
        except:
            raise Exception('Error trying to reach Authorization URL')

        try:
            # response = await got(location, { followRedirect: false })
            response = requests.get(location, allow_redirects=False)
            location = response.headers['location']
            # print('LOCATION2: ' + location)

            regex = 'samlContext=([^&]+)'
            ms = re.search(regex, location)
            samlContext = ms[1]
        except:
            raise Exception('Error trying to follow redirect')

        API_KEY = '3_xRB3jaQ62bVjqXU1omaEsPDVYC0Twi1zfq1zHPu_5HFT0zWkDvZJS97Yw1loJnTm'
        API_KEY2 = '3_QebFXhxEWDc8JhJdBWmvUd1e0AaWJCISbqe4QIHrk_KzNVJFJ4xsJ2UZbl8OIIFY'

        try:
            body = requests.get('https://cdns.gigya.com/js/gigya.js', {
                'apiKey': API_KEY
            }).text
            # print('BODY: ' + body)
            regex = '(\d+-\d-\d+)'
            ms = re.search(regex, body)
            version = ms[0]
            print('VERSION: ' + version)
        except:
            raise Exception('Error trying to extract API version')

        # Extract the cookies used for the Single Sign On
        try:
            ssoCookies = requests.get('https://cdc.daikin.eu/accounts.webSdkBootstrap', {
                'apiKey': API_KEY,
                'sdk': 'js_latest',
                'format': 'json'
            }).headers['set-cookie']
            # print('SSOCOOKIES: ' + ssoCookies)
        except:
            raise Exception('Error trying to extract SSO cookies')

        ssoCookies_arr = ssoCookies.split(', ')
        cookies = ssoCookies_arr[0].split(';')[0].strip() + '; ' + ssoCookies_arr[2].split(';')[0].strip() + '; ' + ssoCookies_arr[4].split(';')[0].strip()
        cookies += '; gig_bootstrap_' + API_KEY + '=cdc_ver4; '
        cookies += 'gig_canary_' + API_KEY2 + '=false; '
        cookies += 'gig_canary_ver_' + API_KEY2 + '=' + version + '; '
        cookies += 'apiDomain_' + API_KEY2 + '=cdc.daikin.eu; ';
        # print('COOKIES: ' + cookies)
        # print('SAMLCONTEXT: ' + samlContext)

        # Login
        login_token = ''
        try:
            headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': cookies
            }
            req_json={
                'loginID': userName,
                'password': password,
                'sessionExpiration':'31536000',
                'targetEnv':'jssdk',
                'include': 'profile,',
                'loginMode': 'standard',
                'riskContext': '{"b0":7527,"b2":4,"b5":1',
                'APIKey': API_KEY,
                'sdk': 'js_latest',
                'authMode': 'cookie',
                'pageURL': 'https://my.daikin.eu/content/daikinid-cdc-saml/en/login.html?samlContext=' + samlContext,
                'sdkBuild': '12208',
                'format': 'json'
            }
            http_args = {}
            http_args['headers'] = headers

            resp = requests.post('https://cdc.daikin.eu/accounts.login', headers=headers, data=req_json)
            response = resp.json()
            print('LOGIN REPLY: {}'.format(response))

            if response is not None and response['errorCode'] == 0 and response['sessionInfo'] is not None and 'login_token' in response['sessionInfo']:
                login_token = response['sessionInfo']['login_token'];
            else:
                raise Exception('Unknown Login error: ' + response['errorDetails'] )
        except:
            raise Exception('Login failed')

        # print('LOGIN TOKEN: ' + login_token)

        samlResponse = ''
        relayState = ''
        expiry = str(int(time.time()) + 3600000)
        cookies = cookies + 'glt_' + API_KEY + '=' + login_token + '; '
        cookies += 'gig_loginToken_' + API_KEY2 + '=' + login_token + '; '
        cookies += 'gig_loginToken_' + API_KEY2 + '_exp=' + expiry + '; '
        cookies += 'gig_loginToken_' + API_KEY2 + '_visited=%2C' + API_KEY + ';'
        _LOGGER.info('COOKIES: %s', cookies)
        # print('COOKIES: ' + cookies)

        try:
            headers = {
                    'cookie': cookies
            }
            req_json={
                'samlContext': samlContext,
                'loginToken': login_token
            }
            response = requests.post('https://cdc.daikin.eu/saml/v2.0/' + API_KEY + '/idp/sso/continue', headers=headers, data=req_json).text
            # print('SAML: {}'.format(response))
            regex = 'name="SAMLResponse" value="([^"]+)"'
            ms = re.search(regex, response)
            samlResponse = ms[1]
            regex = 'name="RelayState" value="([^"]+)"'
            ms = re.search(regex, response)
            relayState = ms[1]

        except:
            raise Exception('Authentication on SAML Identity Provider failed')
        # print('SAMLRESPONSE: ' + samlResponse)
        # print('RELAYSTATE: ' + relayState)


        # Fetch the daikinunified URL
        daikinunified = ''
        try:
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': csrfStateCookie
            }
            req_json={
                'SAMLResponse': samlResponse,
                'RelayState': relayState
            }
            body = 'SAMLResponse=' + samlResponse + '&RelayState=' + relayState # : params.toString(),
            response = requests.post('https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com/saml2/idpresponse', headers=headers, data=req_json, allow_redirects=False)
            daikinunified_url = response.headers['location']
            # print('DAIKINUNIFIED1: {}'.format(response))
            # print('DAIKINUNIFIED2: ' + daikinunified)

            if not 'daikinunified' in daikinunified_url:
                raise Exception('Invalid final Authentication redirect. Location is ' + daikinunified_url)
        except:
            raise Exception('Impossible to retrieve SAML Identity Provider\'s response')

        self.openIdClient.parse_response(
            response=self.openIdClient.message_factory.get_response_type("authorization_endpoint"),
            info=daikinunified_url,
            sformat="urlencoded",
            state=self.state
        )

        self.tokenSet = await self._doAccessTokenRequest(daikinunified_url)
        with open('tokenset.json', 'w') as outfile:
                json.dump(self.tokenSet, outfile)



class DaikinCloudDevice():
    """Class to represent and control one Daikin Cloud Device."""

    def __init__(self, deviceDescription, cloudInstance):
        """Initialize a new Daikin Cloud Device."""
        self.cloud = cloudInstance

        self.setDescription(deviceDescription)
#        _LOGGER.info("Initialized Daikin Cloud Device '%s' (id %s)", self.getValue(None, 'deviceModel'), self.getId())

    def _traverseDatapointStructure(self, obj, data={}, pathPrefix=''):
        """Helper method to traverse the Device object returned by Daikin cloud for subPath datapoints."""
        for key in obj.keys():
            if type(obj[key]) is not dict:
                data[pathPrefix + '/' + key] = obj[key]
            else:
                subKeys = obj[key].keys()
                if key == 'meta' or 'value' in subKeys or 'settable' in subKeys or 'unit' in subKeys:
                    # we found end leaf
                    data[pathPrefix + '/' + key] = obj[key]
                elif type(obj[key]) == dict:
                    # go one level deeper
                    self._traverseDatapointStructure(obj[key], data, pathPrefix + '/' + key)
                else:
                    _LOGGER.error('SOMETHING IS WRONG WITH KEY %s', key)
        return data


    def setDescription(self, desc):
        """Set a device description and parse/traverse data structure."""
        self.desc = desc
        self.managementPoints = {}
        dataPoints = {}

        for mp in self.desc['managementPoints']:
            dataPoints = {}
            for key in mp.keys():
                dataPoints[key] = {}
                if mp[key] == None:
                    continue
                if type(mp[key]) != dict:
                    continue
                if type(mp[key]['value']) != dict or (len(mp[key]['value']) == 1 and 'enabled' in mp[key]['value'] ):
                    dataPoints[key] = mp[key]
                else:
                    dataPoints[key] = self._traverseDatapointStructure(mp[key]['value'], {})
            self.managementPoints[mp['embeddedId']] = dataPoints


    def getId(self):
        """Get Daikin Device UUID."""
        return self.desc['id']

    def getLastUpdated(self):
        """Get the timestamp when data were last updated."""
        return self.desc['lastUpdateReceived']

    def getData(self, managementPoint=None, dataPoint=None, dataPointPath=''):
        """Get a current data object (includes value and meta information)."""
        if managementPoint == None:
            # return all data
            return self.managementPoints
        if not managementPoint in self.managementPoints:
            return None
        if dataPoint == None:
            return self.managementPoints[managementPoint]
        if not dataPoint in self.managementPoints[managementPoint]:
            return None
        if dataPointPath == '':
            # return data from one managementPoint and dataPoint
            return self.managementPoints[managementPoint][dataPoint]
        return self.managementPoints[managementPoint][dataPoint][dataPointPath]


    def getValue(self, managementPoint=None, dataPoint=None, dataPointPath=''):
        """Get the current value of a data object."""
        return self.getData(managementPoint, dataPoint, dataPointPath)['value']

async def main():
    user = sys.argv[1] if len(sys.argv) >= 2 else "nousr"
    pwd = sys.argv[2] if len(sys.argv) >= 3 else "nopwd"
    print ("PARAMS: " + user + " " + pwd)
    controller = DaikinCloudController()
    tokenSet = await controller.retrieveAccessToken(user, pwd)
    devices = await controller.getCloudDevices()
    print('Found ' + str(len(devices))  + ' devices:')
    for dev in devices:
        print('Device (' + dev.getId() + ') Data:')
        print('    modelInfo: ' + dev.getValue('gateway', 'modelInfo'))
        print('    macAddr: ' + dev.getValue('gateway', 'macAddress'))
        print('    fw ver: ' + dev.getValue('gateway', 'firmwareVersion'))

asyncio.run(main())

sys.exit(0)


