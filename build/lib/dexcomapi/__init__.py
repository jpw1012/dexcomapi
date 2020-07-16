"""Sensor for Dexcom packages."""
import logging
import json
from json import JSONEncoder
from datetime import datetime, timedelta, MINYEAR, date
from collections import defaultdict
import asyncio

import http.client
import mimetypes

DATEFORMAT = "%Y-%m-%dT%H:%M:%S"
DOMAIN = "dexcom"
URLROOT = "api.dexcom.com"

_LOGGER = logging.getLogger(__name__)

class ExpiredSessionException(Exception):
    pass

class NoBGDataException(Exception):
    pass

class DexcomSession:
    def __init__(self, user_name, home_url, client_id: str, client_secret: str, code: str = ""):

        self._client_id = client_id
        self._client_secret = client_secret
        self._refreshOverride = code
        self._token_data = None
        self._home_url = home_url
        self._init = False
        self._user = user_name
        self._expires_at = date(MINYEAR, 1, 1)

    def get_name(self):
        return self._user

    def load_session(self):
        # if session is valid, return immediately
        if not self.is_expired():
            return self._token_data

        # if access token is expired or missing, we should refresh
        if self.is_expired():
            # If our refresh token is not valid (expired or does not exist), we should refresh with the configured token
            if not self.can_refresh():
                self._token_data = {"refresh_token": self._refreshOverride}
            _LOGGER.info("Dexcom needs refresh")
            self._refresh_from_token()

        # at this point, we should always have a valid token
        assert not self.is_expired()
        self._init = True
        return self._token_data

    def can_refresh(self):
        return self._token_data is not None and "refresh_token" in self._token_data

    def is_expired(self):
        return self._token_data is None or "access_token" not in self._token_data or datetime.now() > self._expires_at

    def _read_token_response(self, data):
        token_data = json.loads(data)
        if token_data is None or "access_token" not in token_data:
            _LOGGER.error(data)
            assert True == False

        _LOGGER.info("Dexcom reading tokens")
        # _LOGGER.info(data.decode("utf-8"))

        expires_in = token_data['expires_in']
        expires = datetime.now() + timedelta(0, expires_in)
        self._expires_at = expires
        self._token_data = token_data

    def _refresh_from_token(self):
        _LOGGER.info("Dexcom refreshing")

        url = self._home_url
        # _LOGGER.info("Requesting Dexcom auth tokens using code")

        conn = http.client.HTTPSConnection(URLROOT)
        payload = 'client_id={}&client_secret={}&refresh_token={}&grant_type=refresh_token&redirect_uri={}&state=1'
        # TODO: Use state more effectively?
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        conn.request("POST", "/v2/oauth2/token",
                     payload.format(self._client_id, self._client_secret, self._token_data['refresh_token'], url),
                     headers)
        res = conn.getresponse()
        data = res.read()
        self._read_token_response(data)

        return self._token_data

    def load_current_bg(self):

        if self.is_expired():
            raise ExpiredSessionException()

        conn = http.client.HTTPSConnection(URLROOT)
        payload = ''
        headers = {
            'Authorization': 'Bearer {}'.format(self._token_data['access_token'])
        }

        conn.request("GET", "/v2/users/self/egvs?startDate={}&endDate={}".format(
            (datetime.now() - timedelta(0, 0, 0, 0, 10)).strftime(DATEFORMAT), datetime.now().strftime(DATEFORMAT)),
                     payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read())

        last_time = None
        bg = None
        for bgdata in data['egvs']:
            str_time = bgdata["displayTime"]
            time = datetime.strptime(str_time, DATEFORMAT)
            if last_time is None or last_time < time:
                last_time = time
                bg = bgdata

        if bg is None:
            raise NoBGDataException()

        return bg
