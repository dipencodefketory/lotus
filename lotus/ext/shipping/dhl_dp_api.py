# -*- coding: utf-8 -*-

"""DHL_DP_API-CALLS"""

from lotus import env_vars_path
from dotenv import load_dotenv
import requests
import os
from requests.auth import HTTPBasicAuth


load_dotenv(env_vars_path)
base_url_sb = 'https://cig.dhl.de/services/sandbox'
base_url = 'https://cig.dhl.de/services/production'


def get_shipment_tracking(tracking_numbers: list):
    if type(tracking_numbers) != list:
        raise TypeError(f'Variable tracking_number must be of type list. {type(tracking_numbers)} given.')
    xml = f'xml=<?xml version="1.0" encoding="UTF-8"?> <data appname="{os.environ.get("DHL_DP_ZT_USER")}" language-code="de" password="{os.environ.get("DHL_DP_ZT_PW")}" piece-code="{";".join(tracking_numbers)}" request="d-get-piece-detail"/>'
    return requests.get(f'{base_url}/rest/sendungsverfolgung', params=xml, auth=HTTPBasicAuth(os.environ.get('DHL_DP_APP_ID'), os.environ.get('DHL_DP_TOKEN')))


def get_shipment_tracking_sandbox(tracking_numbers: list):
    if type(tracking_numbers) != list:
        raise TypeError(f'Variable tracking_number must be of type list. {type(tracking_numbers)} given.')
    xml = f'<?xml version="1.0" encoding="UTF-8"?> <data appname="zt12345" language-code="de" password="geheim" piece-code="00340434161094015902" request="d-get-piece-detail"/>'
    print(xml)
    return requests.get(f'{base_url_sb}/rest/sendungsverfolgung/', params=xml, auth=HTTPBasicAuth(os.environ.get('DHL_DP_USER_ID'), os.environ.get('DHL_DP_PW')))



