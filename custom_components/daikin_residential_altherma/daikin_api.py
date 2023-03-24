"""Platform for the Daikin AC."""
import base64
import datetime
import functools
import logging
import os
import re
import requests
import time
import asyncio
import json
from oic.oic import Client
from urllib import parse

from homeassistant.util import Throttle
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN, DAIKIN_DEVICES, CONF_TOKENSET

from .daikin_base import Appliance

_LOGGER = logging.getLogger(__name__)

OPENID_CLIENT_ID = "7rk39602f0ds8lk0h076vvijnb"
DAIKIN_CLOUD_URL = "https://daikin-unicloud-prod.auth.eu-west-1.amazoncognito.com"
DAIKIN_ISSUER = "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_SLI9qJpc7"
API_KEY = "3_xRB3jaQ62bVjqXU1omaEsPDVYC0Twi1zfq1zHPu_5HFT0zWkDvZJS97Yw1loJnTm"
API_KEY2 = "3_QebFXhxEWDc8JhJdBWmvUd1e0AaWJCISbqe4QIHrk_KzNVJFJ4xsJ2UZbl8OIIFY"

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=2)


class DaikinApi:
    """Daikin Residential API."""

    def __init__(self, hass, entry):
        """Initialize a new Daikin Residential API."""
        _LOGGER.debug("Initialing Daikin Residential API...")
        self.hass = hass
        self._config_entry = entry
        self.tokenSet = None

        if entry is not None:
            #print("DAMIANO %s", entry.data[CONF_TOKENSET])
            self.tokenSet = entry.data[CONF_TOKENSET].copy()

        configuration = {
            "issuer": DAIKIN_ISSUER,
            "authorization_endpoint": DAIKIN_CLOUD_URL + "/oauth2/authorize",
            "userinfo_endpoint": "userinfo_endpoint",
            "token_endpoint": DAIKIN_CLOUD_URL + "/oauth2/token",
            "token_endpoint_auth_methods_supported": ["none"],
        }

        self.openIdClientId = OPENID_CLIENT_ID
        self.openIdClient = Client(client_id=self.openIdClientId, config=configuration)
        self.openIdStore = {}

        # The Daikin cloud returns old settings if queried with a GET
        # immediately after a PATCH request. Se we use this attribute
        # to skip the first GET if a PATCH request has just been executed.
        self._just_updated = False

        # The following lock is used to serialize http requests to Daikin cloud
        # to prevent receiving old settings while a PATCH is ongoing.
        self._cloud_lock = asyncio.Lock()

        _LOGGER.info("Daikin Residential API initialized.")

    async def doBearerRequest(self, resourceUrl, options=None, refreshed=False):
        if self.tokenSet is None:
            raise Exception("Missing TokenSet. Please repeat Authentication process.")

        if not resourceUrl.startswith("http"):
            resourceUrl = "https://api.prod.unicloud.edc.dknadmin.be" + resourceUrl

        headers = {
            "user-agent": "Daikin/1.6.1.4681 CFNetwork/1209 Darwin/20.2.0",
            "x-api-key": "xw6gvOtBHq5b1pyceadRp6rujSNSZdjx2AqT03iC",
            "Authorization": "Bearer " + self.tokenSet["access_token"],
            "Content-Type": "application/json",
        }

        async with self._cloud_lock:
            _LOGGER.debug("BEARER REQUEST URL: %s", resourceUrl)
            _LOGGER.debug("BEARER REQUEST HEADERS: %s", headers)
            if (
                options is not None
                and "method" in options
                and options["method"] == "PATCH"
            ):
                _LOGGER.debug("BEARER REQUEST JSON: %s", options["json"])
                func = functools.partial(
                    requests.patch, resourceUrl, headers=headers, data=options["json"]
                )
                # res = requests.patch(resourceUrl, headers=headers, data=options["json"])
            else:
                func = functools.partial(requests.get, resourceUrl, headers=headers)
                # res = requests.get(resourceUrl, headers=headers)
            try:
                res = await self.hass.async_add_executor_job(func)
            except Exception as e:
                _LOGGER.error("REQUEST FAILED: %s", e)
                return str(e)
            _LOGGER.debug("BEARER RESPONSE CODE: %s", res.status_code)

        if res.status_code == 200:
            try:
                return res.json()
            except Exception:
                return res.text
        elif res.status_code == 204:
            self._just_updated = True
            return True

        if not refreshed and res.status_code == 401:
            _LOGGER.debug("TOKEN EXPIRED: will refresh it (%s)", res.status_code)
            await self.refreshAccessToken()
            return await self.doBearerRequest(resourceUrl, options, True)

        raise Exception("Communication failed! Status: " + str(res.status_code))

    async def refreshAccessToken(self):
        """Attempt to refresh the Access Token."""
        url = "https://cognito-idp.eu-west-1.amazonaws.com"

        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "x-amz-user-agent": "aws-amplify/0.1.x react-native",
            "User-Agent": "Daikin/1.6.1.4681 CFNetwork/1220.1 Darwin/20.3.0",
        }
        ref_json = {
            "ClientId": OPENID_CLIENT_ID,
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "AuthParameters": {"REFRESH_TOKEN": self.tokenSet["refresh_token"]},
        }
        try:
            func = functools.partial(requests.post, url, headers=headers, json=ref_json)
            res = await self.hass.async_add_executor_job(func)
            # res = requests.post(url, headers=headers, json=ref_json)
        except Exception as e:
            _LOGGER.error("REQUEST FAILED: %s", e)
        _LOGGER.debug("refreshAccessToken response code: %s", res.status_code)
        _LOGGER.debug("refreshAccessToken response: %s", res.json())
        res_json = res.json()
        data = self._config_entry.data.copy()

        if (
            "AuthenticationResult" in res_json
            and res_json["AuthenticationResult"]["AccessToken"] is not None
            and res_json["AuthenticationResult"]["TokenType"] == "Bearer"
        ):
            self.tokenSet["access_token"] = res_json["AuthenticationResult"][
                "AccessToken"
            ]
            self.tokenSet["id_token"] = res_json["AuthenticationResult"]["IdToken"]
            self.tokenSet["expires_at"] = int(
                datetime.datetime.now().timestamp()
            ) + int(res_json["AuthenticationResult"]["ExpiresIn"])
            data[CONF_TOKENSET] = self.tokenSet
            self.hass.config_entries.async_update_entry(
                entry=self._config_entry, data=data
            )
            _LOGGER.debug("TokenSet refreshed.")
            # _LOGGER.debug("TOKENSET REFRESHED: %s", self._config_entry.data)

            return self.tokenSet

        _LOGGER.warning(
            "CANNOT REFRESH TOKENSET (%s): will login again "
            + "and retrieve a new tokenSet.",
            res.status_code,
        )
        try:
            await self.retrieveAccessToken(data[CONF_EMAIL], data[CONF_PASSWORD])
            data[CONF_TOKENSET] = self.tokenSet
            self.hass.config_entries.async_update_entry(
                entry=self._config_entry, data=data
            )
        except Exception:
            raise Exception(
                "Token refresh was not successful! Status: " + str(res.status_code)
            )

    async def _doAuthorizationRequest(self):
        func = functools.partial(self.openIdClient.provider_config, DAIKIN_ISSUER)
        await self.hass.async_add_executor_job(func)
        # self.openIdClient.provider_config(DAIKIN_ISSUER)

        args = {"response_type": ["code"], "scope": "openid"}
        state = (
            base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").replace("=", "")
        )
        _LOGGER.debug("STATE: %s", state)
        args = {
            "authorization_endpoint": DAIKIN_CLOUD_URL + "/oauth2/authorize",
            "userinfo_endpoint": "userinfo_endpoint",
            "response_type": ["code"],
            "scopes": "email,openid,profile",
        }

        self.openIdClient.redirect_uris = ["daikinunified://login"]
        _args, code_verifier = self.openIdClient.add_code_challenge()
        args.update(_args)
        self.openIdStore[state] = {"code_verifier": code_verifier}

        func = functools.partial(
            self.openIdClient.do_authorization_request, request_args=args, state=state
        )
        auth_resp = await self.hass.async_add_executor_job(func)

        self.state = state
        return auth_resp

    async def _doAccessTokenRequest(self, callbackUrl):
        # _LOGGER.debug('_doAccessTokenRequest: %s', callbackUrl)
        params = dict(parse.parse_qsl(parse.urlsplit(callbackUrl).query))
        _LOGGER.debug(
            "VERIFIER: %s", self.openIdStore[params["state"]]["code_verifier"]
        )
        state = self.state

        args = {
            "authorization_endpoint": DAIKIN_CLOUD_URL + "/oauth2/authorize",
            "token_endpoint": DAIKIN_CLOUD_URL + "/oauth2/token",
            "token_endpoint_auth_methods_supported": ["none"],
            # 'userinfo_endpoint': 'userinfo_endpoint',
            "response_type": ["code"],
            "scopes": "email,openid,profile",
            "state": state,
            "token_endpoint_auth_method": "none",  # (default 'client_secret_basic')
        }

        if self.openIdStore[state] is None:
            raise Exception(
                "Cannot decode response for State "
                + state
                + ". Please reload start page and try again!"
            )

        if params["code"] is not None:
            callbackParams = {
                "code_verifier": self.openIdStore[state]["code_verifier"],
                "state": state,
            }
            # _LOGGER.debug('CB PARAMS: %s', callbackParams)
            # _LOGGER.debug('PROVIDER_INFO: %s', self.openIdClient.provider_info)
            func = functools.partial(
                self.openIdClient.do_access_token_request,
                request_args=args,
                extra_args=callbackParams,
                state=state,
                authn_method=None,
            )
            rtk_resp = await self.hass.async_add_executor_job(func)
            # _LOGGER.debug('_RETRIEVETOKENS RESP: %s', rtk_resp)
            new_tokenset = {
                "access_token": rtk_resp["access_token"],
                "refresh_token": rtk_resp["refresh_token"],
                "expires_in": rtk_resp["expires_in"],
                "token_type": rtk_resp["token_type"],
            }
            _LOGGER.debug("TOKENSET RETRIEVED: %s", new_tokenset)
            return new_tokenset
        else:
            raise Exception("Daikin-Cloud: ERROR.")

    async def retrieveAccessToken(self, userName, password):
        _LOGGER.info("Retrieving new TokenSet...")
        # Extract csrf state cookies
        try:
            response = await self._doAuthorizationRequest()
            cookies = response.headers["set-cookie"]
            # _LOGGER.debug('COOKIES: %s', cookies)
            csrfStateCookie = ""
            for cookie in cookies.split(", "):
                for field in cookie.split(";"):
                    if "csrf-state" in field:
                        if csrfStateCookie != "":
                            csrfStateCookie += "; "
                        csrfStateCookie += field.strip()

            # _LOGGER.debug('CSRFSTATECOOKIE COOKIES: %s', csrfStateCookie)
            location = response.headers["location"]
            # _LOGGER.debug('LOCATION: %s', location)
        except Exception as e:
            raise Exception("Error trying to reach Authorization URL: %s", e)

        # Extract SAML Context
        try:
            func = functools.partial(requests.get, location, allow_redirects=False)
            response = await self.hass.async_add_executor_job(func)

            location = response.headers["location"]
            # _LOGGER.debug('LOCATION2: %s', location)

            regex = "samlContext=([^&]+)"
            ms = re.search(regex, location)
            samlContext = ms[1]
        except Exception as e:
            raise Exception("Error trying to follow redirect: %s", e)
        _LOGGER.debug("SAMLCONTEXT: %s", samlContext)

        # Extract API version
        try:
            func = functools.partial(
                requests.get, "https://cdns.gigya.com/js/gigya.js", {"apiKey": API_KEY}
            )
            resp = await self.hass.async_add_executor_job(func)
            body = resp.text
            # _LOGGER.debug('BODY: %s', body)
            regex = "(\d+-\d-\d+)"
            ms = re.search(regex, body)
            version = ms[0]
            _LOGGER.debug("VERSION: %s", version)
        except Exception as e:
            raise Exception("Error trying to extract API version: %s", e)

        # Extract the cookies used for the Single Sign On
        try:
            func = functools.partial(
                requests.get,
                "https://cdc.daikin.eu/accounts.webSdkBootstrap",
                {"apiKey": API_KEY, "sdk": "js_latest", "format": "json"},
            )
            resp = await self.hass.async_add_executor_job(func)
            ssoCookies = resp.headers["set-cookie"]
            # _LOGGER.debug('SSOCOOKIES: %s', ssoCookies)
        except Exception as e:
            raise Exception("Error trying to extract SSO cookies: %s", e)

        ssoCookies_arr = ssoCookies.split(", ")
        cookies = (
            ssoCookies_arr[0].split(";")[0].strip()
            + "; "
            + ssoCookies_arr[2].split(";")[0].strip()
            + "; "
            + ssoCookies_arr[4].split(";")[0].strip()
        )
        cookies += "; gig_bootstrap_" + API_KEY + "=cdc_ver4; "
        cookies += "gig_canary_" + API_KEY2 + "=false; "
        cookies += "gig_canary_ver_" + API_KEY2 + "=" + version + "; "
        cookies += "apiDomain_" + API_KEY2 + "=cdc.daikin.eu; "
        # _LOGGER.debug('COOKIES: %s', cookies)

        # OK, now let's try to Login
        login_token = ""
        try:
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "cookie": cookies,
            }
            req_json = {
                "loginID": userName,
                "password": password,
                "sessionExpiration": "31536000",
                "targetEnv": "jssdk",
                "include": "profile,",
                "loginMode": "standard",
                "riskContext": '{"b0":7527,"b2":4,"b5":1',
                "APIKey": API_KEY,
                "sdk": "js_latest",
                "authMode": "cookie",
                "pageURL": "https://my.daikin.eu/content/daikinid-cdc-saml/en/"
                + "login.html?samlContext="
                + samlContext,
                "sdkBuild": "12208",
                "format": "json",
            }
            http_args = {}
            http_args["headers"] = headers

            func = functools.partial(
                requests.post,
                "https://cdc.daikin.eu/accounts.login",
                headers=headers,
                data=req_json,
            )
            resp = await self.hass.async_add_executor_job(func)
            response = resp.json()
            _LOGGER.debug("LOGIN REPLY: %s", response)

            if (
                response is not None
                and response["errorCode"] == 0
                and response["sessionInfo"] is not None
                and "login_token" in response["sessionInfo"]
            ):
                login_token = response["sessionInfo"]["login_token"]
            else:
                raise Exception("Unknown Login error: " + response["errorDetails"])
        except Exception as e:
            raise Exception("Login failed: %s", e)

        # _LOGGER.debug('LOGIN TOKEN: %s', login_token)

        samlResponse = ""
        relayState = ""
        expiry = str(int(time.time()) + 3600000)
        cookies = cookies + "glt_" + API_KEY + "=" + login_token + "; "
        cookies += "gig_loginToken_" + API_KEY2 + "=" + login_token + "; "
        cookies += "gig_loginToken_" + API_KEY2 + "_exp=" + expiry + "; "
        cookies += "gig_loginToken_" + API_KEY2 + "_visited=%2C" + API_KEY + ";"
        # _LOGGER.debug('COOKIES: %s', cookies)

        try:
            headers = {"cookie": cookies}
            req_json = {"samlContext": samlContext, "loginToken": login_token}
            url = "https://cdc.daikin.eu/saml/v2.0/" + API_KEY + "/idp/sso/continue"
            func = functools.partial(requests.post, url, headers=headers, data=req_json)
            resp = await self.hass.async_add_executor_job(func)
            response = resp.text
            # _LOGGER.debug('SAML: %s', response)
            regex = 'name="SAMLResponse" value="([^"]+)"'
            ms = re.search(regex, response)
            samlResponse = ms[1]
            regex = 'name="RelayState" value="([^"]+)"'
            ms = re.search(regex, response)
            relayState = ms[1]

        except Exception as e:
            raise Exception("Authentication on SAML Identity Provider failed: %s", e)
        # _LOGGER.debug('SAMLRESPONSE: %s', samlResponse)
        # _LOGGER.debug('RELAYSTATE: %s', relayState)

        # Fetch the daikinunified URL
        daikinunified_url = ""
        try:
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "cookie": csrfStateCookie,
            }
            req_json = {"SAMLResponse": samlResponse, "RelayState": relayState}
            body = "SAMLResponse=" + samlResponse + "&RelayState=" + relayState
            url = DAIKIN_CLOUD_URL + "/saml2/idpresponse"
            func = functools.partial(
                requests.post,
                url,
                headers=headers,
                data=req_json,
                allow_redirects=False,
            )
            response = await self.hass.async_add_executor_job(func)
            daikinunified_url = response.headers["location"]
            # _LOGGER.debug('DAIKINUNIFIED1: %s',response)
            # _LOGGER.debug('DAIKINUNIFIED2: %s',daikinunified)

            if "daikinunified" not in daikinunified_url:
                raise Exception(
                    "Invalid final Authentication redirect. Location is "
                    + daikinunified_url
                )
        except Exception as e:
            raise Exception(
                "Impossible to retrieve SAML Identity Provider's response: %s", e
            )

        try:
            self.openIdClient.parse_response(
                response=self.openIdClient.message_factory.get_response_type(
                    "authorization_endpoint"
                ),
                info=daikinunified_url,
                sformat="urlencoded",
                state=self.state,
            )
        except Exception as e:
            raise Exception("Failed to parse response: %s", e)

        try:
            self.tokenSet = await self._doAccessTokenRequest(daikinunified_url)
        except Exception as e:
            raise Exception("Failed to retrieve access token: %s", e)
        _LOGGER.info("New TokenSet successfully retrieved.")

    async def getApiInfo(self):
        """Get Daikin API Info."""
        return await self.doBearerRequest("/v1/info")

    async def getCloudDeviceDetails(self):
        """Get pure Device Data from the Daikin cloud devices."""
        json_puredata = await self.doBearerRequest("/v1/gateway-devices")
        return json_puredata

    async def getCloudDevices(self):
        """Get array of DaikinResidentialDevice objects and get their data."""
        self.json_data = await self.getCloudDeviceDetails()

        res = {}
        for dev_data in self.json_data or []:
            device = Appliance(dev_data, self)
            gateway_model = device.get_value("gateway", "modelInfo")
            device_model = device.desc["deviceModel"]
            _LOGGER.info("Found device '%s' with gateway model '%s'", device_model, gateway_model)
            # Only process use specific models for this integration
            if device_model in ("Altherma", "NDJ"):
                res[dev_data["id"]] = device
            else:
                _LOGGER.info("Device '%s' with gateway model '%s' is filtered out because it is not a supported model", device_model, gateway_model)
        return res

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from Daikin."""
        if self._just_updated:
            self._just_updated = False
            _LOGGER.debug("API UPDATE skipped (just updated from UI)")
            return False

        _LOGGER.debug("API UPDATE")

        self.json_data = await self.getCloudDeviceDetails()
        for dev_data in self.json_data or []:
            #print("DAMIANO dev_data %s", dev_data)
            #print("DAMIANO 'self.hass.data[DOMAIN][DAIKIN_DEVICES]' %s", self.hass.data[DOMAIN][DAIKIN_DEVICES])

            if dev_data["id"] in self.hass.data[DOMAIN][DAIKIN_DEVICES]:
                self.hass.data[DOMAIN][DAIKIN_DEVICES][dev_data["id"]].setJsonData(
                    dev_data
                )
