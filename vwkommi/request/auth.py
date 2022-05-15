"""Module for authentication with VW server"""
import re
from typing import Dict, List
import requests
from vwkommi.settings import VW_PASSWORD, VW_USERNAME

class Auth: # pylint: disable=too-few-public-methods
    """Class taking care of the authentication token"""
    LOGIN_URL = ('https://www.volkswagen.de/app/authproxy/login?fag=vw-de,vwag-weconnect&scope-vw-'
                 'de=profile,address,phone,carConfigurations,dealers,cars,vin,profession&scope-vwag'
                 '-weconnect=openid&prompt-vw-de=login&prompt-vwag-weconnect=none&redirectUrl='
                 'https://www.volkswagen.de/de/besitzer-und-nutzer/myvolkswagen.html')
    IDENTIFIER_URL = ('https://identity.vwgroup.io/signin-service/v1/4fb52a96-2ba3-4f99-a3fc-'
                      '583bb197684b@apps_vw-dilab_com/login/identifier')
    AUTHENTICATION_URL = ('https://identity.vwgroup.io/signin-service/v1/4fb52a96-2ba3-4f99-a3fc-'
                          '583bb197684b@apps_vw-dilab_com/login/authenticate')
    TOKEN_URL = 'https://www.volkswagen.de/app/authproxy/vw-de/tokens'

    def __init__(self) -> None:
        """init"""
        self.token = ''

    def get_token(self) -> str:
        """Gets the authentication token"""
        if not self.token:
            if not self.__do_login():
                return ""
        return self.token

    def __do_login(self) -> bool:
        """Performs the login

        On success _self.token_ is set.
        """
        email = VW_USERNAME
        pwd = VW_PASSWORD

        # create session
        request = requests.session()

        # request login (get cookie)
        req = request.get(Auth.LOGIN_URL)
        if (req.status_code != 200 or not "SESSION" in req.cookies or not 'id="hmac"' in req.text
            or not 'id="csrf"' in req.text or not 'id="input_relayState"' in req.text):
            print("Failed to get cookie")
            return False
        cookie = req.cookies.get_dict()["SESSION"]
        search_values = ["hmac", "csrf", "input_relayState"]
        values = Auth.__get_values(search_values, req.text)
        if len(values) != len(search_values):
            print("Failed to set certain values such as csrf token")
            return False
        hmac, csrf, relay_state = values['hmac'], values['csrf'], values['input_relayState']

        req = request.post(Auth.IDENTIFIER_URL, cookies = {"SESSION": cookie},
                           data = {"hmac": hmac, "_csrf": csrf,
                                   "relayState": relay_state, "email": email})

        if req.status_code != 200 or not '"hmac":' in req.text:
            print("Identify error")
            return False

        tmp = re.findall('"hmac":"([^"]*)"', req.text)
        if not tmp:
            print("Identify error")
            return False
        hmac = tmp[0]

        req = request.post(Auth.AUTHENTICATION_URL, cookies = {"SESSION": cookie},
                           data = {"hmac": hmac, "_csrf": csrf, "relayState": relay_state,
                                   "email": email, "password": pwd})

        if req.status_code != 200 or not "authToken" in req.text:
            print("Authenticate error")
            return False

        req = request.get("https://www.volkswagen.de/")
        tmp = request.cookies.get_dict()
        if "csrf_token" not in tmp:
            print("CSRF error")
            return False
        csrf = tmp["csrf_token"]
        req = request.get(Auth.TOKEN_URL, headers = {"x-csrf-token": csrf})
        if not "access_token" in req.text:
            print("ACCESS_TOKEN error")
            return False
        tmp = re.findall('"access_token":"([^"]*)"', req.text)

        self.token = 'Bearer ' + tmp[0]
        return True

    @staticmethod
    def __get_values(fields: List[str], request_text: str) -> Dict:
        return_dict = {}
        for field in fields:
            tmp = re.findall('id="' + field + '"[^>]*value="([^"]*)"', request_text, re.IGNORECASE)
            if not tmp:
                tmp = re.findall('value="([^"]*)"[^>]*id="' + field + '"', request_text,
                                 re.IGNORECASE)
            if tmp:
                tmp = tmp[0]
            else:
                continue
            return_dict[field] = tmp
        return return_dict
