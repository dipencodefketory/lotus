# -*- coding: utf-8 -*-

from lotus import *
from requests.auth import HTTPBasicAuth

load_dotenv(env_vars_path)
base_url = f'https://import.idealo.com/shop/{environ.get("IDEALO_BUSINESS_SHOP_ID")}'


def get_access_token():
    """
    Basic function to generate an access-token for further API-calls.
    :return: dictionary of the general form
        {'access_token': token, 'token_type': 'bearer', 'expires_in': 3599, 'scope': 'MERCHANTORDERAPI:READ_ALL MERCHANTORDERAPI:WRITE_ALL', 'shop_id': <shop_id>}.
    """
    header = {'Content-Type': 'application/x-www-form-urlencoded'}
    auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,
                         auth=HTTPBasicAuth(environ.get('IDEALO_BUSINESS_CLIENT_ID'), environ.get('IDEALO_BUSINESS_CLIENT_PW')), data={'grant_type': 'client_credentials'})
    try:
        auth = auth.json()
        return auth
    except Exception:
        raise ConnectionError('Idealo-Access-Token could not be generated.')


def generate_price_report(auth):
    header = {"Authorization": "Bearer " + auth['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8', 'scope': auth['scope']}
    return requests.post(url=f"https://businessapi.idealo.com/api/v1/shops/{environ.get('IDEALO_BUSINESS_SHOP_ID')}/price-reports", headers=header, json={"site": "IDEALO_DE"})


def get_price_report(auth, report_id):
    header = {"Authorization": "Bearer " + auth['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8', 'scope': auth['scope']}
    return requests.get(url=f'https://businessapi.idealo.com/api/v1/shops/{environ.get("IDEALO_BUSINESS_SHOP_ID")}/price-reports/{report_id}/download', headers=header)


def generate_offer_report(auth, type: str = 'ALL_OFFERS'):
    header = {'Authorization': 'Bearer ' + auth['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8', 'scope': auth['scope']}
    return requests.post(url=f"https://businessapi.idealo.com/api/v1/shops/{environ.get('IDEALO_BUSINESS_SHOP_ID')}//offer-reports", headers=header, json={'site': 'IDEALO_DE', 'offerReportType': type})


def get_offer_report(auth, report_id):
    header = {"Authorization": "Bearer " + auth['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8', 'scope': auth['scope']}
    return requests.get(url=f'https://businessapi.idealo.com/api/v1/shops/{environ.get("IDEALO_BUSINESS_SHOP_ID")}/offer-reports/{report_id}', headers=header)


def download_offer_report(auth, report_id):
    header = {"Authorization": "Bearer " + auth['access_token'], 'Accept': 'application/json', 'Content-Type': 'application/json; charset=UTF-8', 'scope': auth['scope']}
    return requests.get(url=f'https://businessapi.idealo.com/api/v1/shops/{environ.get("IDEALO_BUSINESS_SHOP_ID")}/offer-reports/{report_id}/download', headers=header)
