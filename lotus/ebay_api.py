# -*- coding: utf-8 -*-

"""EBAY API-CALLS"""

from lotus import env_vars_path, db
import basismodels
from dotenv import load_dotenv
from ebaysdk.trading import Connection as tradingConn
from typing import List, Dict
from lookup import basic_return_policy
from datetime import datetime
from urllib.parse import unquote
import requests
import os
import webbrowser
import base64


dict_dict = Dict[str, Dict]
dict_list = List[Dict]
str_list = List[str]

load_dotenv(env_vars_path)


def get_item(trading_api: tradingConn, item_id: str):
    data = {'ItemID': item_id}
    return 200, trading_api.execute('GetItem', data)


def get_access_rules(trading_api: tradingConn):
    return 200, trading_api.execute('GetApiAccessRules')


def put_product(trading_api: tradingConn, currency: str, description: str, dispatch_time_max: int, image_array: str_list, mpn: str, brand: str, ean: str, quantity: int, sku: str, price: float, title: str,
                shipping_service_dict: dict, vat: float, feature_array: dict_list = None, isbn: str = '', upc: str = '', category_id: str = ''):
    if not feature_array:
        feature_array = []
    else:
        if type(feature_array) != list:
            raise TypeError('Optional variable feature_array must be of type list. Initial value is [].')
        else:
            for item in feature_array:
                if type(item) != dict:
                    raise TypeError('Items of feature_array must be of type dict.')
                else:
                    if len(item) != 2:
                        raise ValueError('Items of feature_array must have exactly two keys.')
                    else:
                        for key in item:
                            if key not in ['Name', 'Value']:
                                raise KeyError('Items of feature_array must only contain the keys Name and Value.')
                            else:
                                if type(item[key]) != str:
                                    raise TypeError('Dictionaries in feature_array must only contain elements of type string.')
    if type(image_array) != list:
        raise TypeError('Variable image_array must be of type list.')
    else:
        for item in image_array:
            if type(item) != str:
                raise TypeError('Items of image_array must be of type str.')
    if type(shipping_service_dict) != dict:
        raise TypeError('Variable shipping_service_dict must be of type list.')
    else:
        for key in shipping_service_dict:
            if key not in ['InternationalShippingServiceOption', 'ShippingServiceOptions']:
                raise TypeError('Keys of shipping_service_dict must either "InternationalShippingServiceOption" or "ShippingServiceOptions".')
            else:
                for el in shipping_service_dict[key]:
                    sub_keys = el.keys()
                    if 'ShippingService' not in sub_keys or 'ShippingServiceCost' not in sub_keys or 'FreeShipping' not in sub_keys:
                        raise ValueError('For any shipping-service the keys "ShippingService", "ShippingServiceCost" and "FreeShipping" must be specified.')
                    elif type(el['ShippingServiceCost']) != float:
                        raise TypeError('All values for key "ShippingServiceCost" must be of type float.')
                    elif el['ShippingServiceCost'] < 0:
                        raise TypeError('All values for key "ShippingServiceCost" must be non-negative.')
                    elif el['FreeShipping'] not in [0, 1]:
                        raise ValueError('All values for key "FreeShipping" must be either 0 or 1.')
    if type(trading_api) != tradingConn:
        raise TypeError('Variable trading_api must be of type trading_conn.')
    elif type(description) != str:
        raise TypeError('Variable description must be of type str.')
    elif type(dispatch_time_max) != int:
        raise TypeError('Variable dispatch_time_max must be of type int.')
    elif type(mpn) != str:
        raise TypeError('Variable mpn must be of type str.')
    elif type(brand) != str:
        raise TypeError('Variable brand must be of type str.')
    elif type(ean) != str:
        raise TypeError('Variable ean must be of type str.')
    elif type(sku) != str:
        raise TypeError('Variable sku must be of type str.')
    elif type(price) != float:
        raise TypeError('Variable price must be of type float.')
    elif type(title) != str:
        raise TypeError('Variable title must be of type str.')
    elif type(vat) != float:
        raise TypeError('Variable vat must be of type float.')
    elif type(isbn) != str:
        raise TypeError('Optional variable isbn must be of type str. Initial value is "".')
    elif type(upc) != str:
        raise TypeError('Optional variable upc must be of type str. Initial value is "".')
    elif type(quantity) != int:
        raise TypeError('Optional variable quantity must be of type int. Initial value is -1.')
    elif type(category_id) != str:
        raise TypeError('Optional variable quantity must be of type str. Initial value is "".')
    else:
        if len(description) > 500000:
            raise ValueError('Variable description can not have more than 500000 characters.')
        elif dispatch_time_max not in [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]:
            raise ValueError('Variable dispatch_time_max must have one of the following values: 0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40.')
        elif len(brand) > 65:
            raise ValueError('Variable brand can not have more than 65 characters.')
        elif len(ean) < 8 or len(ean) > 13:
            raise ValueError('Variable ean must have at least 8 and at most 13 characters.')
        elif len(sku) > 50:
            raise ValueError('Variable sku can not have more than 50 characters.')
        elif price <= 0:
            raise ValueError('Variable price must be positive.')
        elif len(title) > 80:
            raise ValueError('Variable title can not have more than 80 characters.')
        elif vat < 0:
            raise ValueError('Variable vat must be non-negative.')
        elif isbn and (len(isbn) != 13 or isbn[:3] not in ['978', '979']):
            raise ValueError('Optional variable isbn must have exactly 13 characters and start with either "978" or "979". Initial value is "".')
        elif len(category_id) > 10:
            raise ValueError('Optional variable category_id can not have more than 10 characters. Initial value is "".')
        else:
            feature_array.append({'Name': 'Marke', 'Value': brand})
            feature_array.append({'Name': 'Herstellernummer', 'Value': mpn})
            upload_dict = {'Item':
                {
                    'BuyerRequirementDetails': {'ShipToRegistrationCountry': True,
                                                'MaximumItemRequirements': {
                                                    'MaximumItemCount': 10
                                                }},
                    'ConditionID': 1000,
                    'Country': 'DE',
                    'Currency': currency,
                    'Description': f'<![CDATA[{description}]]>',
                    'DispatchTimeMax': dispatch_time_max,
                    'HitCounter': 'BasicStyle',
                    'ItemSpecifics': {'NameValueList': feature_array},
                    'InventoryTrackingMethod': 'SKU',
                    'PictureDetails': {'PictureURL': image_array},
                    'ListingDuration': 'GTC',
                    'ListingType': 'FixedPriceItem',
                    'PictureSource': 'Vendor',
                    'PostalCode': '10247',
                    'ProductListingDetails':
                        {
                            'BrandMPN': {'MPN': mpn, 'Brand': brand},
                            'EAN': ean,
                            'IncludeStockPhotoURL': False,
                            'UseStockPhotoURLAsGallery': False
                        },
                    'Quantity': quantity,
                    'ReturnPolicy':
                        {
                            'Description': basic_return_policy,
                            'InternationalReturnsAcceptedOption': 'ReturnsNotAccepted',
                            'RefundOption': 'MoneyBackOrExchange',
                            'ReturnsAcceptedOption': 'ReturnsAccepted',
                            'ReturnsWithinOption': 'Months_1',
                            'ShippingCostPaidByOption': 'Buyer'
                        },
                    'ShippingDetails': shipping_service_dict,
                    'SKU': sku,
                    'StartPrice': price,
                    'Title': title,
                    'VATDetails': {'VATPercent': vat}
                }
            }
            if dispatch_time_max <= 1:
                upload_dict['Item']['eBayPlus'] = True
            if isbn:
                upload_dict['Item']['ProductListingDetails']['ISBN'] = isbn
            if upc:
                upload_dict['Item']['ProductListingDetails']['UPC'] = upc
            if category_id:
                upload_dict['Item']['PrimaryCategory'] = {'CategoryID': category_id}
            return trading_api.execute('AddFixedPriceItem', upload_dict)


def patch_product(trading_api: tradingConn, marketplace_offer_id: str, description: str = None, description_revise_mode: str = None, dispatch_time_max: int = None, feature_array: dict_list = None,
                  image_array: str_list = None, mpn: str = None, brand: str = None, ean: str = None, isbn: str = None, upc: str = None, quantity: int = None, category_id: str = None, sku: str = None,
                  price: float = None, title: str = None, shipping_service_dict: dict = None, vat: float = None):
    if not feature_array:
        feature_array = []
    else:
        if type(feature_array) != list:
            raise TypeError('Optional variable feature_array must be of type list. Initial value is [].')
        else:
            for item in feature_array:
                if type(item) != dict:
                    raise TypeError('Items of feature_array must be of type dict.')
                else:
                    if len(item) != 2:
                        raise ValueError('Items of feature_array must have exactly two keys.')
                    else:
                        for key in item:
                            if key not in ['Name', 'Value']:
                                raise KeyError('Items of feature_array must only contain the keys Name and Value.')
                            if type(key) != str:
                                raise TypeError('Keys of feature_array-item must be of type str.')
                            else:
                                if type(item[key]) != str:
                                    raise TypeError('Dictionaries in feature_array must only contain elements of type string.')
    if not image_array:
        image_array = []
    else:
        if type(image_array) != list:
            raise TypeError('Variable image_array must be of type list. Initial value is [].')
        else:
            for item in image_array:
                if type(item) != str:
                    raise TypeError('Items of image_array must be of type str.')
    if not shipping_service_dict:
        shipping_service_dict = {}
    else:
        if type(shipping_service_dict) != dict:
            raise TypeError('Variable shipping_service_dict must be of type list.')
        else:
            for key in shipping_service_dict:
                if key not in ['InternationalShippingServiceOption', 'ShippingServiceOptions']:
                    raise TypeError('Keys of shipping_service_dict must either "InternationalShippingServiceOption" or "ShippingServiceOptions".')
                else:
                    for el in shipping_service_dict[key]:
                        sub_keys = el.keys()
                        if 'ShippingService' not in sub_keys or 'ShippingServiceCost' not in sub_keys or 'FreeShipping' not in sub_keys:
                            raise ValueError('For any shipping-service the keys "ShippingService", "ShippingServiceCost" and "FreeShipping" must be specified.')
                        elif type(el['ShippingServiceCost']) != float:
                            raise TypeError('All values for key "ShippingServiceCost" must be of type float.')
                        elif el['ShippingServiceCost'] < 0:
                            raise TypeError('All values for key "ShippingServiceCost" must be non-negative.')
                        elif el['FreeShipping'] not in [0, 1]:
                            raise ValueError('All values for key "FreeShipping" must be either 0 or 1.')
    if type(trading_api) != tradingConn:
        raise TypeError('Variable trading_api must be of type trading_conn.')
    elif marketplace_offer_id is None:
        raise TypeError('Please provide a valid marketplace_offer_id.')
    elif type(marketplace_offer_id) != str:
        raise TypeError('Variable marketplace_offer_id must be of type str.')
    elif description is not None and type(description) != str:
        raise TypeError('Optional variable description must be of type str. Initial value is "".')
    elif description_revise_mode is not None and type(description_revise_mode) != str:
        raise TypeError('Optional variable description_revise_mode must be of type str. Initial value is "".')
    elif dispatch_time_max is not None and type(dispatch_time_max) != int:
        raise TypeError('Optional variable dispatch_time_max must be of type int. Initial value is -1.')
    elif mpn is not None and type(mpn) != str:
        raise TypeError('Optional variable mpn must be of type str. Initial value is "".')
    elif brand is not None and type(brand) != str:
        raise TypeError('Optional variable brand must be of type str. Initial value is "".')
    elif ean is not None and type(ean) != str:
        raise TypeError('Optional variable ean must be of type str. Initial value is "".')
    elif isbn is not None and type(isbn) != str:
        raise TypeError('Optional variable isbn must be of type str. Initial value is "".')
    elif upc is not None and type(upc) != str:
        raise TypeError('Optional variable upc must be of type str. Initial value is "".')
    elif quantity is not None and type(quantity) != int:
        raise TypeError('Optional variable quantity must be of type int. Initial value is -1.')
    elif category_id is not None and type(category_id) != str:
        raise TypeError('Optional variable quantity must be of type str. Initial value is "".')
    elif sku is not None and type(sku) != str:
        raise TypeError('Optional variable sku must be of type str. Initial value is "".')
    elif price is not None and type(price) != float:
        raise TypeError('Variable price must be of type float.')
    elif title is not None and type(title) != str:
        raise TypeError('Optional variable title must be of type str. Initial value is "".')
    elif vat is not None and type(vat) != float:
        raise TypeError('Variable vat must be of type float.')
    else:
        if description is not None and len(description) > 500000:
            raise ValueError('Optional variable description can not have more than 500000 characters. Initial value is "".')
        if description_revise_mode is not None and description_revise_mode not in ['Append', 'Prepend', 'Replace']:
            raise ValueError('Optional variable description_revise_mode must have one of the following values: "Append", "Prepend", "Replace". Initial value is "".')
        if description and not description_revise_mode:
            raise SystemError('Variable description_revise_mode must be specified, when updating the optional variable description.')
        if dispatch_time_max not in [None, 0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]:
            raise ValueError('Optional variable dispatch_time_max must have one of the following values: None, 0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40. Initial value is -1.')
        if brand is not None:
            if len(brand) > 65:
                raise ValueError('Optional variable brand can not have more than 65 characters. Initial value is "".')
        if ean is not None:
            if ean and (len(ean) < 8 or len(ean) > 13):
                raise ValueError('Optional variable ean must have at least 8 and at most 13 characters. Initial value is "".')
        if isbn is not None:
            if len(isbn) != 13 or isbn[:3] not in ['978', '979']:
                raise ValueError('Optional variable isbn must have exactly 13 characters and start with either "978" or "979". Initial value is "".')
        if category_id is not None:
            if len(category_id) > 10:
                raise ValueError('Optional variable category_id can not have more than 10 characters. Initial value is "".')
        if sku is not None:
            if len(sku) > 50:
                raise ValueError('Optional variable sku can not have more than 50 characters. Initial value is "".')
        if price is not None:
            if price <= 0:
                raise ValueError('Variable price must be positive.')
        if title is not None:
            if len(title) > 80:
                raise ValueError('Optional variable title can not have more than 80 characters. Initial value is "".')
        if vat is not None:
            if vat < 0:
                raise ValueError('Variable vat must be non-negative.')
        update_dict = {'Item': {'ItemID': marketplace_offer_id, 'ShippingServiceOptions': 'Worldwide', 'InventoryTrackingMethod': 'SKU'}}
        if description:
            update_dict['Item']['Description'] = f'<![CDATA[{description}]]>'
            update_dict['Item']['DescriptionReviseMode'] = description_revise_mode
        if dispatch_time_max is not None:
            update_dict['Item']['DispatchTimeMax'] = dispatch_time_max
        if brand:
            feature_array.append({'Name': 'Marke', 'Value': brand})
        if mpn:
            feature_array.append({'Name': 'Herstellernummer', 'Value': mpn})
        if feature_array:
            update_dict['Item']['ItemSpecifics'] = {'NameValueList': feature_array}
        if image_array:
            update_dict['Item']['PictureDetails'] = {'PictureURL': image_array}
        pl_details = {}
        if ean:
            pl_details['EAN'] = ean
        if isbn:
            pl_details['ISBN'] = isbn
        if upc:
            pl_details['UPC'] = upc
        if ean or isbn or upc:
            update_dict['Item']['ProductListingDetails'] = pl_details
        if quantity is not None:
            update_dict['Item']['Quantity'] = quantity
        if category_id:
            update_dict['Item']['PrimaryCategory'] = {'CategoryID': category_id}
        if sku:
            update_dict['Item']['SKU'] = sku
        if price:
            update_dict['Item']['StartPrice'] = price
        if title:
            update_dict['Item']['Title'] = title
        if shipping_service_dict:
            update_dict['Item']['ShippingDetails'] = shipping_service_dict
        if vat:
            update_dict['Item']['VATDetails'] = {'VATPercent': vat}
        if dispatch_time_max is not None:
            if dispatch_time_max <= 1:
                update_dict['Item']['eBayPlus'] = True
            else:
                update_dict['Item']['eBayPlus'] = False
        return trading_api.execute('ReviseFixedPriceItem', update_dict)


def relist_product(trading_api: tradingConn, marketplace_offer_id: str, price: float, description: str = None, description_revise_mode: str = None, dispatch_time_max: int = None, feature_array: dict_list = None,
                   image_array: str_list = None, mpn: str = None, brand: str = None, ean: str = None, isbn: str = None, upc: str = None, quantity: int = None, category_id: str = None, sku: str = None,
                   title: str = None, shipping_service_dict: dict = None, vat: float = None):
    if not feature_array:
        feature_array = []
    else:
        if type(feature_array) != list:
            raise TypeError('Optional variable feature_array must be of type list. Initial value is [].')
        else:
            for item in feature_array:
                if type(item) != dict:
                    raise TypeError('Items of feature_array must be of type dict.')
                else:
                    if len(item) != 2:
                        raise ValueError('Items of feature_array must have exactly two keys.')
                    else:
                        for key in item:
                            if key not in ['Name', 'Value']:
                                raise KeyError('Items of feature_array must only contain the keys Name and Value.')
                            if type(key) != str:
                                raise TypeError('Keys of feature_array-item must be of type str.')
                            else:
                                if type(item[key]) != str:
                                    raise TypeError('Dictionaries in feature_array must only contain elements of type string.')
    if not image_array:
        image_array = []
    else:
        if type(image_array) != list:
            raise TypeError('Variable image_array must be of type list. Initial value is [].')
        else:
            for item in image_array:
                if type(item) != str:
                    raise TypeError('Items of image_array must be of type str.')
    if not shipping_service_dict:
        shipping_service_dict = {}
    else:
        if type(shipping_service_dict) != dict:
            raise TypeError('Variable shipping_service_dict must be of type list.')
        else:
            for key in shipping_service_dict:
                if key not in ['InternationalShippingServiceOption', 'ShippingServiceOptions']:
                    raise TypeError('Keys of shipping_service_dict must either "InternationalShippingServiceOption" or "ShippingServiceOptions".')
                else:
                    for el in shipping_service_dict[key]:
                        sub_keys = el.keys()
                        if 'ShippingService' not in sub_keys or 'ShippingServiceCost' not in sub_keys or 'FreeShipping' not in sub_keys:
                            raise ValueError('For any shipping-service the keys "ShippingService", "ShippingServiceCost" and "FreeShipping" must be specified.')
                        elif type(el['ShippingServiceCost']) != float:
                            raise TypeError('All values for key "ShippingServiceCost" must be of type float.')
                        elif el['ShippingServiceCost'] < 0:
                            raise TypeError('All values for key "ShippingServiceCost" must be non-negative.')
                        elif el['FreeShipping'] not in [0, 1]:
                            raise ValueError('All values for key "FreeShipping" must be either 0 or 1.')
    if type(trading_api) != tradingConn:
        raise TypeError('Variable trading_api must be of type trading_conn.')
    elif marketplace_offer_id is None:
        raise TypeError('Please provide a valid marketplace_offer_id.')
    elif type(marketplace_offer_id) != str:
        raise TypeError('Variable marketplace_offer_id must be of type str.')
    elif price is None:
        raise TypeError('Please provide a valid price.')
    elif type(price) != float:
        raise TypeError('Variable price must be of type float.')
    elif description is not None and type(description) != str:
        raise TypeError('Optional variable description must be of type str. Initial value is "".')
    elif description_revise_mode is not None and type(description_revise_mode) != str:
        raise TypeError('Optional variable description_revise_mode must be of type str. Initial value is "".')
    elif dispatch_time_max is not None and type(dispatch_time_max) != int:
        raise TypeError('Optional variable dispatch_time_max must be of type int. Initial value is -1.')
    elif mpn is not None and type(mpn) != str:
        raise TypeError('Optional variable mpn must be of type str. Initial value is "".')
    elif brand is not None and type(brand) != str:
        raise TypeError('Optional variable brand must be of type str. Initial value is "".')
    elif ean is not None and type(ean) != str:
        raise TypeError('Optional variable ean must be of type str. Initial value is "".')
    elif isbn is not None and type(isbn) != str:
        raise TypeError('Optional variable isbn must be of type str. Initial value is "".')
    elif upc is not None and type(upc) != str:
        raise TypeError('Optional variable upc must be of type str. Initial value is "".')
    elif quantity is not None and type(quantity) != int:
        raise TypeError('Optional variable quantity must be of type int. Initial value is -1.')
    elif category_id is not None and type(category_id) != str:
        raise TypeError('Optional variable quantity must be of type str. Initial value is "".')
    elif sku is not None and type(sku) != str:
        raise TypeError('Optional variable sku must be of type str. Initial value is "".')
    elif title is not None and type(title) != str:
        raise TypeError('Optional variable title must be of type str. Initial value is "".')
    elif vat is not None and type(vat) != float:
        raise TypeError('Variable vat must be of type float.')
    else:
        if description is not None and len(description) > 500000:
            raise ValueError('Optional variable description can not have more than 500000 characters. Initial value is "".')
        if description_revise_mode is not None and description_revise_mode not in ['Append', 'Prepend', 'Replace']:
            raise ValueError('Optional variable description_revise_mode must have one of the following values: "Append", "Prepend", "Replace". Initial value is "".')
        if description and not description_revise_mode:
            raise SystemError('Variable description_revise_mode must be specified, when updating the optional variable description.')
        if dispatch_time_max not in [None, 0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]:
            raise ValueError('Optional variable dispatch_time_max must have one of the following values: None, 0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40. Initial value is -1.')
        if brand is not None:
            if len(brand) > 65:
                raise ValueError('Optional variable brand can not have more than 65 characters. Initial value is "".')
        if ean is not None:
            if ean and (len(ean) < 8 or len(ean) > 13):
                raise ValueError('Optional variable ean must have at least 8 and at most 13 characters. Initial value is "".')
        if isbn is not None:
            if len(isbn) != 13 or isbn[:3] not in ['978', '979']:
                raise ValueError('Optional variable isbn must have exactly 13 characters and start with either "978" or "979". Initial value is "".')
        if category_id is not None:
            if len(category_id) > 10:
                raise ValueError('Optional variable category_id can not have more than 10 characters. Initial value is "".')
        if sku is not None:
            if len(sku) > 50:
                raise ValueError('Optional variable sku can not have more than 50 characters. Initial value is "".')
        if price <= 0:
            raise ValueError('Variable price must be positive.')
        if title is not None:
            if len(title) > 80:
                raise ValueError('Optional variable title can not have more than 80 characters. Initial value is "".')
        if vat is not None:
            if vat < 0:
                raise ValueError('Variable vat must be non-negative.')
        update_dict = {'Item': {'ItemID': marketplace_offer_id, 'ShippingServiceOptions': 'Worldwide', 'InventoryTrackingMethod': 'SKU', 'StartPrice': price}}
        if description:
            update_dict['Item']['Description'] = f'<![CDATA[{description}]]>'
            update_dict['Item']['DescriptionReviseMode'] = description_revise_mode
        if dispatch_time_max is not None:
            update_dict['Item']['DispatchTimeMax'] = dispatch_time_max
        if brand:
            feature_array.append({'Name': 'Marke', 'Value': brand})
        if mpn:
            feature_array.append({'Name': 'Herstellernummer', 'Value': mpn})
        if feature_array:
            update_dict['Item']['ItemSpecifics'] = {'NameValueList': feature_array}
        if image_array:
            update_dict['Item']['PictureDetails'] = {'PictureURL': image_array}
        pl_details = {}
        if ean:
            pl_details['EAN'] = ean
        if isbn:
            pl_details['ISBN'] = isbn
        if upc:
            pl_details['UPC'] = upc
        if ean or isbn or upc:
            update_dict['Item']['ProductListingDetails'] = pl_details
        if quantity is not None:
            update_dict['Item']['Quantity'] = quantity
        if category_id:
            update_dict['Item']['PrimaryCategory'] = {'CategoryID': category_id}
        if sku:
            update_dict['Item']['SKU'] = sku
        if title:
            update_dict['Item']['Title'] = title
        if shipping_service_dict:
            update_dict['Item']['ShippingDetails'] = shipping_service_dict
        if vat:
            update_dict['Item']['VATDetails'] = {'VATPercent': vat}
        if dispatch_time_max is not None:
            if dispatch_time_max <= 1:
                update_dict['Item']['eBayPlus'] = True
            else:
                update_dict['Item']['eBayPlus'] = False
        return trading_api.execute('RelistFixedPriceItem', update_dict)


def delete_product(trading_api: tradingConn, marketplace_offer_id: str, reason: str = 'NotAvailable'):
    """
    Function to end FixedPriceItem-auctions on ebay.
    :param trading_api: Active Ebay-Trading-API-Connection constructed through ebaysdk.trading.Connection
    :param marketplace_offer_id: Offer-ID specified by Ebay
    :param reason: Reason for ending the auction. Possible values are: Incorrect, LostOrBroken, NotAvailable, OtherListingError, ProductDeleted, SellToHighBidder, Sold.
    :return:
    """
    return trading_api.execute('EndFixedPriceItem', {'EndingReason': reason, 'ItemID': marketplace_offer_id})

#******************************************************************************************************************************************************************************************************#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# BUY-API                                                                                                                                                                                      BUY-API #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#******************************************************************************************************************************************************************************************************#


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# BROWSE                                                                                                                                                                                       BROWSE #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_item_summary(q: str = None, gtin: str = None, charity_ids: str = None, field_groups: str = None, auto_correct: str = None, category_ids: str = None, limit: str = None, offset: str = None, epid: str = None):
    if q is not None and type(q) != str:
        raise TypeError('Variable q must be of type str.')
    if gtin is not None and type(gtin) != str:
        raise TypeError('Variable gtin must be of type str.')
    if charity_ids is not None and type(charity_ids) != str:
        raise TypeError('Variable charity_ids must be of type str.')
    if field_groups is not None and type(field_groups) != str:
        raise TypeError('Variable field_groups must be of type str.')
    if auto_correct is not None and type(auto_correct) != str:
        raise TypeError('Variable auto_correct must be of type str.')
    if category_ids is not None and type(category_ids) != str:
        raise TypeError('Variable category_ids must be of type str.')
    if limit is not None and type(limit) != str:
        raise TypeError('Variable limit must be of type str.')
    if offset is not None and type(offset) != str:
        raise TypeError('Variable offset must be of type str.')
    if epid is not None and type(epid) != str:
        raise TypeError('Variable epid must be of type str.')
    params = {}
    if q is not None:
        params['q'] = q
    if gtin is not None:
        params['gtin'] = gtin
    if charity_ids is not None:
        params['charity_ids'] = charity_ids
    if field_groups is not None:
        params['fieldgroups'] = field_groups
    if auto_correct is not None:
        params['auto_correct'] = auto_correct
    if category_ids is not None:
        params['category_ids'] = category_ids
    if limit is not None:
        params['limit'] = limit
    if offset is not None:
        params['offset'] = offset
    if epid is not None:
        params['epid'] = epid
    if params:
        return requests.get('https://api.ebay.com/buy/browse/v1/item_summary/search?filter=excludeSellers:{lotus-icafe}&filter=conditionIds:{1000}&filter=sellers:{lotus-icafe}&',
                            headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}', 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_DE'},  params=params)
    else:
        raise SystemError('Provide at least one parameter.')


def get_own_item_summary(q: str = None, gtin: str = None, charity_ids: str = None, field_groups: str = None, auto_correct: str = None, category_ids: str = None, limit: str = None, offset: str = None, epid: str = None):
    if q is not None and type(q) != str:
        raise TypeError('Variable q must be of type str.')
    if gtin is not None and type(gtin) != str:
        raise TypeError('Variable gtin must be of type str.')
    if charity_ids is not None and type(charity_ids) != str:
        raise TypeError('Variable charity_ids must be of type str.')
    if field_groups is not None and type(field_groups) != str:
        raise TypeError('Variable field_groups must be of type str.')
    if auto_correct is not None and type(auto_correct) != str:
        raise TypeError('Variable auto_correct must be of type str.')
    if category_ids is not None and type(category_ids) != str:
        raise TypeError('Variable category_ids must be of type str.')
    if limit is not None and type(limit) != str:
        raise TypeError('Variable limit must be of type str.')
    if offset is not None and type(offset) != str:
        raise TypeError('Variable offset must be of type str.')
    if epid is not None and type(epid) != str:
        raise TypeError('Variable epid must be of type str.')
    params = {}
    if q is not None:
        params['q'] = q
    if gtin is not None:
        params['gtin'] = gtin
    if charity_ids is not None:
        params['charity_ids'] = charity_ids
    if field_groups is not None:
        params['fieldgroups'] = field_groups
    if auto_correct is not None:
        params['auto_correct'] = auto_correct
    if category_ids is not None:
        params['category_ids'] = category_ids
    if limit is not None:
        params['limit'] = limit
    if offset is not None:
        params['offset'] = offset
    if epid is not None:
        params['epid'] = epid
    if params:
        return requests.get('https://api.ebay.com/buy/browse/v1/item_summary/search?filter=sellers:{lotus-icafe}&',
                            headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}', 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_DE'},  params=params)
    else:
        raise SystemError('Provide at least one parameter.')

#******************************************************************************************************************************************************************************************************#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# SELL-API                                                                                                                                                                                    SELL-API #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#******************************************************************************************************************************************************************************************************#


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ACCESS                                                                                                                                                                                        ACCESS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_auth_code():
    webbrowser.open_new(f"https://auth.ebay.com/oauth2/authorize?client_id={os.environ['EBAY_CLIENT_ID']}&response_type=code&redirect_uri={os.environ['EBAY_REDIRECT_URI']}&scope=https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly")
    url = input('enter url: ')
    url = unquote(url)
    start_number = url.find('code=') + len('code=')
    end_number = url.find('&expires_in')
    auth_code = url[start_number:end_number]
    return auth_code


def get_access_token(auth_code):
    r = requests.post('https://api.ebay.com/identity/v1/oauth2/token?',
                      headers={'Content-Type': 'application/x-www-form-urlencoded',
                               'Authorization': f'Basic {base64.b64encode(bytes(os.environ["EBAY_CLIENT_ID"] + ":" + os.environ["EBAY_CLIENT_SECRET"], "utf-8")).decode("utf-8") }'},
                      data={'grant_type': 'authorization_code', 'code': auth_code, 'redirect_uri': os.environ["EBAY_REDIRECT_URI"]}
                      )
    return r


def refresh_access_token(refresh_token):
    r = requests.post('https://api.ebay.com/identity/v1/oauth2/token?',
                      headers={'Content-Type': 'application/x-www-form-urlencoded',
                               'Authorization': f'Basic {base64.b64encode(bytes(os.environ["EBAY_CLIENT_ID"] + ":" + os.environ["EBAY_CLIENT_SECRET"], "utf-8")).decode("utf-8") }'},
                      data={'grant_type': 'refresh_token', 'refresh_token': refresh_token,
                            'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly'}
                      )
    return r

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ANALYTICS                                                                                                                                                                                  ANALYTICS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_rate_limits(api_name: str, api_context: str = None):
    params = {'api_name': api_name}
    if api_context is not None:
        params['api_context'] = api_context
    return requests.get('https://api.ebay.com/developer/analytics/v1_beta/rate_limit/?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, params=params)


def get_user_rate_limits(api_name: str, api_context: str = None):
    params = {'api_name': api_name}
    if api_context is not None:
        params['api_context'] = api_context
    return requests.get('https://api.ebay.com/developer/analytics/v1_beta/user_rate_limit/?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, params=params)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ACCOUNT                                                                                                                                                                                      ACCOUNT #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_payments_program():
    return requests.get('https://api.ebay.com/sell/account/v1/payments_program/EBAY_DE/EBAY_PAYMENTS', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def create_fulfillment_policy(description: str, handling_time: int, name: str):
    fulfillment_policy = {
        "categoryTypes":
            [
                {
                    "default": False,
                    "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
                }
            ],
        "description": description,
        "handlingTime":
            {
                "unit": "DAY",
                "value": handling_time
            },
        "marketplaceId": "EBAY_DE",
        "name": name,
        "shippingOptions":
            [
                {
                    "costType": "FLAT_RATE",
                    "optionType": "ShippingOptionTypeEnum : [DOMESTIC,INTERNATIONAL]",
                    "packageHandlingCost":
                        {
                            "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                            "value": "string"
                        },
                    "rateTableId": "string",
                    "shippingServices":
                        [
                            {
                                "additionalShippingCost":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    },
                                "buyerResponsibleForPickup": "boolean",
                                "buyerResponsibleForShipping": "boolean",
                                "freeShipping": "boolean",
                                "shippingCarrierCode": "string",
                                "shippingCost":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    },
                                "shippingServiceCode": "string",
                                "shipToLocations":
                                    {
                                        "regionExcluded": [
                                            {
                                                "regionName": "string",
                                                "regionType": "RegionTypeEnum : [COUNTRY,COUNTRY_REGION,STATE_OR_PROVINCE...]"
                                            }
                                        ],
                                        "regionIncluded":
                                            [
                                                {
                                                    "regionName": "string",
                                                    "regionType": "RegionTypeEnum : [COUNTRY,COUNTRY_REGION,STATE_OR_PROVINCE...]"
                                                }
                                            ]
                                    },
                                "sortOrder": "integer",
                                "surcharge":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    }
                            }
                        ]
                }
            ]
    }
    r = requests.post('https://api.ebay.com/sell/account/v1/fulfillment_policy?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, json=fulfillment_policy)
    return r


def del_fulfillment_policy(fulfillment_policy_id: str):
    return requests.delete(f'https://api.ebay.com/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_fulfillment_policies():
    return requests.get('https://api.ebay.com/sell/account/v1/fulfillment_policy?marketplace_id=EBAY_DE', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_fulfillment_policy(fulfillment_policy_id: str = None, fulfillment_policy_name: str = None):
    if fulfillment_policy_id is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    elif fulfillment_policy_name is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/fulfillment_policy/get_by_policy_name?marketplace_id=EBAY_DE&name={fulfillment_policy_name}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    else:
        raise SystemError('Provide either a fulfillment_policy_id or fulfillment_policy_name.')


def create_payment_policy(description: str, name: str):
    payment_policy = {
        "categoryTypes":
            [
                {
                    "default": True,
                    "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
                }
            ],
        "description": description,
        "immediatePay": True,
        "marketplaceId": "EBAY_DE",
        "name": name
    }
    r = requests.post('https://api.ebay.com/sell/account/v1/payment_policy?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, json=payment_policy)
    return r


def del_payment_policy(payment_policy_id: str):
    return requests.delete(f'https://api.ebay.com/sell/account/v1/payment_policy/{payment_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_payment_policies():
    return requests.get('https://api.ebay.com/sell/account/v1/payment_policy?marketplace_id=EBAY_DE', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_payment_policy(payment_policy_id: str = None, payment_policy_name: str = None):
    if payment_policy_id is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/payment_policy/{payment_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    elif payment_policy_name is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/payment_policy/get_by_policy_name?marketplace_id=EBAY_DE&name={payment_policy_name}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    else:
        raise SystemError('Provide either a payment_policy_id or payment_policy_name.')


def create_return_policy(description: str, name: str):
    return_policy = {
        "categoryTypes":
            [
                {
                    "default": True,
                    "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
                }
            ],
        "description": description,
        "internationalOverride":
            {
                "returnsAccepted": False
            },
        "marketplaceId": "EBAY_DE",
        "name": name,
        "refundMethod": "MONEY_BACK",
        "returnInstructions": basic_return_policy,
        "returnPeriod":
            {
                "unit": "MONTH",
                "value": 1
            },
        "returnsAccepted": True,
        "returnShippingCostPayer": "BUYER"
    }
    r = requests.post('https://api.ebay.com/sell/account/v1/return_policy?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, json=return_policy)
    return r


def del_return_policy(return_policy_id: str):
    return requests.delete(f'https://api.ebay.com/sell/account/v1/return_policy/{return_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_return_policies():
    return requests.get('https://api.ebay.com/sell/account/v1/return_policy?marketplace_id=EBAY_DE', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_return_policy(return_policy_id: str = None, return_policy_name: str = None):
    if return_policy_id is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/return_policy/{return_policy_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    elif return_policy_name is not None:
        return requests.get(f'https://api.ebay.com/sell/account/v1/return_policy/get_by_policy_name?marketplace_id=EBAY_DE&name={return_policy_name}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})
    else:
        raise SystemError('Provide either a return_policy_id or return_policy_name.')


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# INVENTORY                                                                                                                                                                                  INVENTORY #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

# INVENTORY-ITEM ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- INVENTORY-ITEM #


def bulk_get_inventory_item(skus: list):
    return requests.post('https://api.ebay.com/sell/inventory/v1/bulk_get_inventory_item?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, json={'requests': skus})


def put_inventory_item(sku: str, product_id: int, brand: str = None, description: str = None, ean: str = None, feature_dict: dict = None, image_array: list = None, mpn: str = None, quantity: int = None, title: str = None):
    if type(sku) != str:
        raise TypeError('Variable sku must be of type str.')
    if type(product_id) != int:
        raise TypeError('Variable product_id must be of type int.')
    if brand is not None and type(brand) != str:
        raise TypeError('Variable brand must be of type str.')
    if description is not None and type(description) != str:
        raise TypeError('Variable description must be of type str.')
    if ean is not None and type(ean) != str:
        raise TypeError('Variable ean must be of type str.')
    if feature_dict is not None and type(feature_dict) != dict:
        raise TypeError('Variable feature_array must be of type dict.')
    if image_array is not None and type(image_array) != list:
        raise TypeError('Variable image_array must be of type str_list.')
    if mpn is not None and type(mpn) != str:
        raise TypeError('Variable mpn must be of type str.')
    if quantity is not None and type(quantity) != int:
        raise TypeError('Variable quantity must be of type int.')
    if title is not None and type(title) != str:
        raise TypeError('Variable title must be of type str.')
    inv_item = {}
    if brand is not None or feature_dict is not None or ean is not None or image_array is not None or mpn is not None or title is not None:
        p_dict = {}
        if brand is not None:
            p_dict['brand'] = brand
        if brand is not None:
            p_dict['aspects'] = feature_dict
        if brand is not None:
            p_dict['ean'] = [ean]
        if brand is not None:
            p_dict['imageUrls'] = image_array
        if brand is not None:
            p_dict['mpn'] = mpn
        if brand is not None:
            p_dict['title'] = title
        inv_item['product'] = p_dict
    if quantity is not None:
        inv_item['availability'] = {
            "pickupAtLocationAvailability":
                [
                    {
                        "availabilityType": "IN_STOCK",
                        "merchantLocationKey": "DE_10247",
                        "quantity": quantity
                    }
                ],
            "shipToLocationAvailability":
                {
                    "availabilityDistributions":
                        [
                            {
                                "merchantLocationKey": "DE_10247",
                                "quantity": quantity
                            }
                        ],
                    "quantity": quantity
                }
        }
    if inv_item:
        inv_item["condition"] = "NEW"
        r = requests.put(f'https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}', 'Content-Language': 'de-DE'}, json=inv_item)
        db.session.add(basismodels.ProductUpdateLog(url=f'https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}?', method='PUT', data=str(inv_item), response=r.text, status_code=r.status_code, product_id=product_id, marketplace_id=2))
        db.session.commit()
        return r
    else:
        raise SystemError('Provide at least one attribute.')


def delete_inventory_item(sku: str):
    return requests.delete(f'https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_inventory_item(sku: str):
    return requests.get(f'https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_inventory_items(limit: int = 25, offset: int = 0):
    return requests.get('https://api.ebay.com/sell/inventory/v1/inventory_item?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, params={'limit': limit, 'offset': offset})


# LISTING ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ LISTING #


def bulk_migrate_listing(listing_ids: list):
    return requests.post('https://api.ebay.com/sell/inventory/v1/bulk_migrate_listing?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, json={'requests': listing_ids})


# LOCATION ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- LOCATION #


def get_inventory_locations():
    return requests.get(f'https://api.ebay.com/sell/inventory/v1/location?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


# OFFER ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- OFFER #


def create_offer(currency: str, description: str, fulfillment_policy_id: str, quantity: int, sku: str, price: float, shipping_services: list, vat: float, product_id: int, category_id: str = ''):
    offer = {
        "availableQuantity": quantity,
        "categoryId": category_id,
        "format": "FIXED_PRICE",
        "hideBuyerDetails": False,
        "includeCatalogProductDetails": True,
        "listingDescription": description,
        "listingDuration": "GTC",
        "listingPolicies":
            {
                "eBayPlusIfEligible": True,
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": "182110163015",
                "returnPolicyId": "207405999015",
                "shippingCostOverrides": shipping_services
            },
        "marketplaceId": "EBAY_DE",
        "merchantLocationKey": "DE_10247",
        "pricingSummary":
            {
                "price":
                    {
                        "currency": currency,
                        "value": str(price)
                    }
            },
        "quantityLimitPerBuyer": quantity,
        "sku": sku,
        "tax":
            {
                "applyTax": True,
                "vatPercentage": vat
            }
    }
    r = requests.post('https://api.ebay.com/sell/inventory/v1/offer?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}', 'Content-Language': 'de-DE'}, json=offer)
    db.session.add(basismodels.ProductUpdateLog(url=f'https://api.ebay.com/sell/inventory/v1/offer?', method='POST', data=str(offer), response=r.text, status_code=r.status_code, product_id=product_id, marketplace_id=2))
    db.session.commit()
    return r


def delete_offer(offer_id: str):
    return requests.delete(f'https://api.ebay.com/sell/inventory/v1/offer/{offer_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def get_offer(sku: str):
    return requests.get('https://api.ebay.com/sell/inventory/v1/offer?', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'}, params={'sku': sku})


def publish_offer(offer_id: str):
    return requests.post(f'https://api.ebay.com/sell/inventory/v1/offer/{offer_id}/publish/', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def withdraw_offer(offer_id: str):
    return requests.post(f'https://api.ebay.com/sell/inventory/v1/offer/{offer_id}/withdraw/', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}'})


def update_offer(offer_id: str, currency: str, description: str, fulfillment_policy_id: str, quantity: int, price: float, shipping_services: list, vat: float, product_id: int, category_id: str = ''):
    offer = {
        "availableQuantity": quantity,
        "categoryId": category_id,
        "hideBuyerDetails": False,
        "includeCatalogProductDetails": True,
        "listingDescription": description,
        "listingDuration": "GTC",
        "listingPolicies":
            {
                "eBayPlusIfEligible": True,
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": "182110163015",
                "returnPolicyId": "207405999015",
                "shippingCostOverrides": shipping_services
            },
        "merchantLocationKey": "DE_10247",
        "pricingSummary":
            {
                "price":
                    {
                        "currency": currency,
                        "value": str(price)
                    }
            },
        "quantityLimitPerBuyer": quantity,
        "tax":
            {
                "applyTax": True,
                "vatPercentage": vat
            }
    }
    r = requests.put(f'https://api.ebay.com/sell/inventory/v1/offer/{offer_id}', headers={'Authorization': f'Bearer {os.environ["EBAY_OAUTH_TOKEN"]}', 'Content-Language': 'de-DE'}, json=offer)
    db.session.add(basismodels.ProductUpdateLog(url=f'https://api.ebay.com/sell/inventory/v1/offer/{offer_id}', method='PUT', data=str(offer), response=r.text, status_code=r.status_code, product_id=product_id, marketplace_id=2))
    db.session.commit()
    return r
