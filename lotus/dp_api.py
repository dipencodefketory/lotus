# -*- coding: utf-8 -*-

"""DEUTSCHE-POST API-CALLS"""

from lotus import env_vars_path
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import base64
import xml.etree.ElementTree as ETree
import json


dict_dict = Dict[str, Dict]
dict_list = List[Dict]
str_list = List[str]

load_dotenv(env_vars_path)

base_url = 'https://api-sandbox.dhl.com/wapo'


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ACCESS                                                                                                                                                                                        ACCESS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_access():
    """
    Valid for 5 h.
    :return: access-information in JSON-format, e.g.
    {
        "access_token": "vzoJsASlFm0rfz3HsZEWC69lgQcytQQqWJvk9eBL3cMF8j7W4ny4Dh",
        "token_type": "Bearer",
        "expires_in": 18000,
        "scope": "dpilabel dpitracking"
    }
    """
    b64_code = base64.b64encode(f'{os.environ["DP_SANDBOX_PORTO_EMAIL"]}:{os.environ["DP_SANDBOX_PORTO_PW"]}'.encode("utf8")).decode("utf8")
    headers = {'Content-Type': 'application/json', 'Accept': '', 'KEY_PHASE': '1', 'PARTNER_ID': os.environ["DP_SANDBOX_PARTNER_ID"], 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be',
               'Authorization': f'Basic {b64_code}'}
    r = requests.get(f'{base_url}/v1/auth/accesstoken', headers=headers)
    print(r.text)
    tree = ETree.fromstring(r.text)
    els = [el.tag for el in tree.iter()]
    els = list(set(els))
    token_tag = ''
    for el in els:
        if 'userToken' in el:
            token_tag = el
    token = tree.find(f'.//{token_tag}')
    if token is not None:
        return token.text
    else:
        'NO_TOKEN'


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ORDERS                                                                                                                                                                                        ORDERS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def create_order(access_token, product: str, recipient: str, address_line_1: str, city: str, destination_country: str, postal_code: str, recipient_email: str, recipient_phone: str, shipment_gross_weight: int,
                 address_line_2: str = '', state: str = '', awb_copy_count: int = 3, order_status: str = "FINALIZE"):
    items = {
        "product": product,
        "recipient": recipient,
        "addressLine1": address_line_1,
        "postalCode": postal_code,
        "city": city,
        "destinationCountry": destination_country,
        "shipmentGrossWeight": shipment_gross_weight,
        "senderName": "Onlineshop Önal Lotus iCafe",
        "senderAddressLine1": "Proskauer Str. 32",
        "senderCountry": "DE",
        "senderCity": "Berlin",
        "senderPostalCode": "10247",
        "shipmentNaturetype": "SALE_GOODS",
        "shipmentCurrency": "EUR"
    }
    if address_line_2:
        items["addressLine2"] = address_line_2
    if state:
        items["state"] = state
    if recipient_email:
        items["recipientEmail"] = recipient_email
    if recipient_phone:
        items["recipientPhone"] = recipient_phone
    data = {
        "customerEkp": os.environ["DP_CLIENT_EKP"],
        "orderStatus": order_status,
        "paperwork": {
            "contactName": "Faruk Önal",
            "awbCopyCount": awb_copy_count
        },
        "items": [items]
    }
    headers = {"Content-Type": "application/json", "KEY_PHASE": "1", "PARTNER_ID": "DP_LT", "REQUEST_TIMESTAMP": "16082018-122210", "PARTNER_SIGNATURE": "9d7c35be", "Authorization": f"Bearer {access_token}"}
    print(f'{base_url}/shipping/v1/orders')
    print(json.dumps(data))
    print(json.dumps(headers))
    return requests.post(f'{base_url}/shipping/v1/orders', json=data, headers=headers)


def get_order(access_token, order_id: str):
    headers = {'Content-Type': 'application/json', 'KEY_PHASE': '1', 'PARTNER_ID': 'DP_LT', 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be', 'Authorization': f'Bearer {access_token}'}
    return requests.get(f'{base_url}/shipping/v1/orders/{order_id}', headers=headers)


def finalize_order(access_token, order_id: str, awb_copy_count: int):
    data = {
            "contactName": "Faruk Önal",
            "awbCopyCount": awb_copy_count
    }
    headers = {'Content-Type': 'application/json', 'KEY_PHASE': '1', 'PARTNER_ID': 'DP_LT', 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be', 'Authorization': f'Bearer {access_token}'}
    return requests.post(f'{base_url}/shipping/v1/orders/{order_id}/finalization', data=data, headers=headers)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ITEMS                                                                                                                                                                                          ITEMS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
def get_item(access_token, item_id: int):
    headers = {'Content-Type': 'application/json', 'KEY_PHASE': '1', 'PARTNER_ID': 'DP_LT', 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be', 'Authorization': f'Bearer {access_token}'}
    return requests.get(f'{base_url}/dpi/shipping/v1/items/{item_id}', headers=headers)


def update_item(access_token, product: str, recipient: str, address_line1: str, city: str, destination_country: str, item_id: int, postal_code: str, shipment_gross_weight: int, content_piece_hs_code: str,
                content_piece_description: str, content_piece_value: float, content_piece_net_weight: int, content_piece_amount: int, shipment_nature_type: str = 'SALE_GOODS'):
    data = {
        "product": product,
        # "serviceLevel": "PRIORITY",
        "recipient": recipient,
        "addressLine1": address_line1,
        "city": city,
        "destinationCountry": destination_country,
        "id": item_id,
        # "custRef": "REF-2361890-AB",
        # "recipientPhone": "+4935120681234",
        # "recipientFax": "+4935120681234",
        # "recipientEmail": "alfred.j.quack@somewhere.eu",
        # "addressLine2": "Hinterhaus",
        # "addressLine3": "1. Etage",
        # "state": "Sachsen",
        "postalCode": postal_code,
        # "shipmentAmount": 100,
        # "shipmentCurrency": "EUR",
        "shipmentGrossWeight": shipment_gross_weight,
        "shipmentNaturetype": shipment_nature_type,
        "contents": [
            {
                "contentPieceHsCode": content_piece_hs_code,
                "contentPieceDescription": content_piece_description,
                "contentPieceValue": '%0.20f' % content_piece_value,
                "contentPieceNetweight": content_piece_net_weight,
                "contentPieceOrigin": "DE",
                "contentPieceAmount": content_piece_amount
            }
        ]
    }
    headers = {'Content-Type': 'application/json', 'KEY_PHASE': '1', 'PARTNER_ID': 'DP_LT', 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be', 'Authorization': f'Bearer {access_token}'}
    return requests.put(f'{base_url}/dpi/shipping/v1/items/{item_id}', data=data, headers=headers)


def delete_item(access_token, item_id: int):
    headers = {'Content-Type': 'application/json', 'KEY_PHASE': '1', 'PARTNER_ID': 'DP_LT', 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be', 'Authorization': f'Bearer {access_token}'}
    return requests.delete(f'{base_url}/dpi/shipping/v1/items/{item_id}', headers=headers)
'''

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# SHIPMENTS                                                                                                                                                                                  SHIPMENTS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
def get_shipment_awb(access_token, awb: str):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    return requests.get(f'https://api-qa.deutschepost.com/dpi/shipping/v1/shipments/{awb}', headers=headers)


def get_awb_labels(access_token, awb: str):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    return requests.get(f'https://api-qa.deutschepost.com/dpi/shipping/v1/shipments/{awb}/awblabels', headers=headers)
'''


def get_item_labels(access_token, awb: str):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/pdf', 'KEY_PHASE': '1', 'PARTNER_ID': os.environ["DP_SANDBOX_PARTNER_ID"], 'REQUEST_TIMESTAMP': '16082018-122210', 'PARTNER_SIGNATURE': '9d7c35be',
               'Authorization': f'Bearer {access_token}'}
    return requests.get(f'https://api-sandbox.dhl.com/wapo/shipping/v1/shipments/{awb}/itemlabels', headers=headers)
