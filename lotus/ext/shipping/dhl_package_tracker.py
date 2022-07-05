# -*- coding: utf-8 -*-

"""DHL-PACKAGE-TRACKER-CALLS"""

from lotus import env_vars_path
from dotenv import load_dotenv
import requests
import os


load_dotenv(env_vars_path)
headers = {'DHL-API-Key': os.environ["DHL_PT_KEY"]}


def get_shipment_tracking_dhl_u(tracking_number: str):
    if type(tracking_number) != str:
        raise TypeError(f'Variable tracking_number must be of type str. {type(tracking_number)} given.')
    return requests.get('https://api-eu.dhl.com/track/shipments', params={'trackingNumber': tracking_number}, headers=headers)
