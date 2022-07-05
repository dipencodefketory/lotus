# -*- coding: utf-8 -*-

from lotus import env_vars_path
import requests
from os import environ
from dotenv import load_dotenv

load_dotenv(env_vars_path)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# DEEP_L                                                                                                                                                                                        DEEP_L #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def dl_translate(text: str, target_lang: str = 'DE'):
    data = {'target_lang': target_lang, 'auth_key': environ.get('DEEP_L_AUTH_KEY'), 'text': text}
    return requests.post(url='https://api-free.deepl.com/v2/translate', data=data)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# DEEP_L PRO                                                                                                                                                                                DEEP_L PRO #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def dl_pro_translate(text: str, target_lang: str = 'DE'):
    data = {'target_lang': target_lang, 'auth_key': environ.get('DEEP_L_PRO_AUTH_KEY'), 'text': text}
    return requests.post(url='https://api.deepl.com/v2/translate', data=data)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ADDRESS_VALIDATOR                                                                                                                                                                  ADDRESS_VALIDATOR #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def validate_address(data: dict):
    """
    :param data: dictionary of the general form
    {'CountryCode':	two-letter ISO 3166-1 country code (string), 'XX' for international,
    'StreetAddress':	street/housenumber/building, may include unit/apt etc. (string),
    'AdditionalAddressInfo':	building/unit/apt/floor etc. [optional] (string),
    'City':	city or locality (city, district) [optional] (string),
    'PostalCode':	zip/postal code [optional] (string)}
    :return: requests response object.
    """
    data['APIKey'] = environ.get('ADDRESS_VALIDATOR_AUTH_KEY')
    return requests.post(url='https://api.address-validator.net/api/verify', data=data)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# REMOVE_BG                                                                                                                                                                                  REMOVE_BG #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def remove_background(image: str):
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_url': environ.get('IMAGE_SERVER') + image},
        data={'image_url': environ.get('IMAGE_SERVER') + image, 'size': 'full', 'crop': 'true', 'crop_margin': '5%', 'bg_color': 'white', 'type': 'product'},
        headers={'X-Api-Key': environ.get('REMOVE_BG_TOKEN')},
    )
    if response.status_code == requests.codes.ok:
        with open(f'{image.split(".")[0]}_a.png', 'wb') as out:
            out.write(response.content)
        return f'{image.split(".")[0]}_a.png'
    else:
        print("Error:", response.status_code, response.text)
        return 'ERROR'

