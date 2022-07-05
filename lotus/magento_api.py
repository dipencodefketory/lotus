# -*- coding: utf-8 -*-
"""MAGENTO API-CALLS
1. CATEGORIES
2. PRODUCTS
3. ORDERS
"""

import requests
from requests_oauthlib import OAuth1
from datetime import datetime
import json
from typing import List

int_list = List[int]

# GLOBAL VARIABLES
MAGENTO_CONSUMER_KEY = '3n93vbhctzr5rwjin6yreppxilmza1bz'
MAGENTO_CONSUMER_SECRET = 'hx0dysh3fil760u3pdal3mx89p5vzcmu'
MAGENTO_TOKEN = '58anjxnadr6akjsm4zj3lw7z8zw05c9o'
MAGENTO_SECRET = 'jy0726tdergskvf5hv0p45el37rtcjzl'
MAGENTO_API_URL = 'http://87.106.126.163/rest/V1/'

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


def get_auth():
    return OAuth1(client_key=MAGENTO_CONSUMER_KEY, client_secret=MAGENTO_CONSUMER_SECRET, resource_owner_key=MAGENTO_TOKEN, resource_owner_secret=MAGENTO_SECRET)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# CATEGORIES                                                                                                                                                                                CATEGORIES #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def post_category(category_id: int, parent_id: int, position: int, level: int, children: str, available_sort_by: list, path: str, created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M"),
                  updated_at: str = datetime.now().strftime("%Y-%m-%d %H:%M"), include_in_menu: bool = True, is_active: bool = True, custom_attributes: list = None):
    if type(category_id) != int:
        print('Variable category_id must be of type int.')
        raise TypeError
    elif type(parent_id) != int:
        print('Variable parent_id must be of type int.')
        raise TypeError
    elif type(position) != int:
        print('Variable position must be of type int.')
        raise TypeError
    elif type(level) != int:
        print('Variable level must be of type int.')
        raise TypeError
    elif type(children) != str:
        print('Variable children must be of type str.')
        raise TypeError
    elif type(available_sort_by) != list:
        print('Variable available_sort_by must be of type list.')
        raise TypeError
    elif type(path) != str:
        print('Variable path must be of type str.')
        raise TypeError
    elif type(created_at) != str:
        print('Optional variable created_at must be of type str.')
        raise TypeError
    elif type(updated_at) != str:
        print('Optional variable updated_at must be of type str.')
        raise TypeError
    elif type(include_in_menu) != bool:
        print('Optional variable include_in_menu must be of type bool.')
        raise TypeError
    elif type(is_active) != bool:
        print('Optional variable is_active must be of type bool.')
        raise TypeError
    elif custom_attributes is not None and type(custom_attributes) != list:
        print('Optional variable custom_attributes must be None or of type list.')
        raise TypeError
    else:
        category = {"id": category_id, "parent_id": parent_id, "name": "string", "is_active": is_active, "position": position, "level": level, "children": children, "created_at": created_at,
                    "updated_at": updated_at, "path": path, "available_sort_by": available_sort_by, "include_in_menu": include_in_menu, "custom_attributes": custom_attributes}
        return requests.post(f'{MAGENTO_API_URL}/categories', headers=headers, data=json.dumps(category))


def post_product_to_category(auth, sku: str, position: int, category_id: str):
    if type(sku) != str:
        print('Variable sku must be of type str.')
        raise TypeError
    elif type(position) != int:
        print('Variable position must be of type int.')
        raise TypeError
    elif type(category_id) != str:
        print('Variable category_id must be of type str.')
        raise TypeError
    else:
        link = {
            "productLink":
                {
                    "sku": sku,
                    "position": position,
                    "category_id": category_id,
                }
        }
        return requests.post(f'{MAGENTO_API_URL}/categories/{category_id}/products', headers=headers, data=json.dumps(link))


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# PRODUCTS                                                                                                                                                                                    PRODUCTS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def post_product(auth, product_id: int, sku: str, ean: str, name: str, price: float, qty: int, type_id: str = 'simple', category_id: str = '', description: str = '', short_description: str = '',
                 weight: float = .0, status: int = 1, visibility: int = 4, meta_title: str = '', meta_keyword: str = '', meta_description: str = '', is_in_stock: bool = True,
                 attribute_set_id: int = 4, product_links: list = None, media_gallery_entries: list = None):
    if type(product_id) != int:
        print('Variable product_id must be of type int.')
        raise TypeError
    elif type(sku) != str:
        print('Variable sku must be of type str.')
        raise TypeError
    elif type(ean) != str:
        print('Variable ean must be of type str.')
        raise TypeError
    elif type(name) != str:
        print('Variable name must be of type str.')
        raise TypeError
    elif type(price) != float:
        print('Variable price must be of type float.')
        raise TypeError
    elif type(qty) != int:
        print('Variable qty must be of type int.')
        raise TypeError
    elif type(type_id) != str:
        print('Optional variable type_id must be of type str.')
        raise TypeError
    elif type(category_id) != str:
        print('Optional variable category_id must be of type str.')
        raise TypeError
    elif description != None and type(description) != str:
        print('Optional variable description must be of type str.')
        raise TypeError
    elif short_description != None and type(short_description) != str:
        print('Optional variable short_description must be of type str.')
        raise TypeError
    elif type(weight) != float:
        print('Optional variable weight must be of type float.')
        raise TypeError
    elif type(status) != int:
        print('Optional variable status must be of type int.')
        raise TypeError
    elif type(visibility) != int:
        print('Optional variable visibility must be of type int.')
        raise TypeError
    elif type(meta_title) != str:
        print('Optional variable meta_title must be of type str.')
        raise TypeError
    elif type(meta_keyword) != str:
        print('Optional variable meta_keyword must be of type str.')
        raise TypeError
    elif type(meta_description) != str:
        print('Optional variable meta_description must be of type str.')
        raise TypeError
    elif type(is_in_stock) != bool:
        print('Optional variable is_in_stock must be of type bool.')
        raise TypeError
    elif type(attribute_set_id) != int:
        print('Optional variable attribute_set_id must be of type int.')
        raise TypeError
    elif product_links != None and type(product_links) != list:
        print('Optional variable product_links must be None or of type list.')
        raise TypeError
    elif media_gallery_entries != None and type(media_gallery_entries) != list:
        print('Optional variable media_gallery_entries must be None or of type list.')
        raise TypeError
    else:
        if status not in [0, 1]:
            print('Invalid status. Possible values are 0, 1.')
            raise ValueError
        elif visibility not in range(1, 5):
            print('Invalid visibility. Possible values are 1, 2, 3, 4.')
            raise ValueError
        elif type_id not in ["simple", "virtual", "configurable", "grouped", "bundle", "downloadable"]:
            print(f'Invalid type_id. Possible values are "simple", "virtual", "configurable", "grouped", "bundle", "downloadable". ({type_id} was given.)')
            raise ValueError
        elif len(ean) != 13:
            print(f'Variable ean must have exactly 13 characters. ({ean} with length {len(ean)} was given.)')
            raise ValueError
        else:
            product = {
                'product': {
                    'id': product_id,
                    'sku': sku,
                    'name': name,
                    'price': price,
                    'status': status,
                    'visibility': visibility,
                    'type_id': type_id,
                    'weight': weight,
                    'custom_attributes': [
                        {'attribute_code': 'description', 'value': description},
                        {'attribute_code': 'short_description', 'value': short_description},
                        {'attribute_code': 'ean', 'value': ean}
                    ],
                    'extension_attributes': {
                        'stock_item': {
                            'qty': qty,
                            'is_in_stock': is_in_stock,
                            'is_qty_decimal': False,
                            'show_default_notification_message': False,
                            "use_config_min_qty": True,
                            "min_qty": 0,
                            "use_config_min_sale_qty": 1,
                            "min_sale_qty": 1,
                            "use_config_max_sale_qty": True,
                            "max_sale_qty": qty,
                            "use_config_backorders": True,
                            "backorders": 0,
                            "use_config_notify_stock_qty": True,
                            "notify_stock_qty": 1,
                            "use_config_qty_increments": True,
                            "qty_increments": 0,
                            "use_config_enable_qty_inc": True,
                            "enable_qty_increments": False,
                            "use_config_manage_stock": False,
                            "manage_stock": True,
                            "low_stock_date": None,
                            "is_decimal_divided": False,
                            "stock_status_changed_auto": 0
                            }
                    }
                },
                'saveOptions': False
            }
        if attribute_set_id:
            product['product']['attribute_set_id'] = attribute_set_id
        if category_id:
            product['product']['extension_attributes']['category_links'] = [{'category_id': category_id}]
        if product_links:
            product['product']['product_links'] = product_links
        if media_gallery_entries:
            product['product']['media_gallery_entries'] = media_gallery_entries
        if meta_title:
            product['product']['meta_title'] = meta_title
        if meta_keyword:
            product['product']['meta_keyword'] = meta_keyword
        if meta_description:
            product['product']['meta_description'] = meta_description
        return requests.post(url=f'{MAGENTO_API_URL}products', headers=headers, data=json.dumps(product), auth=auth)


def post_product_price(auth, sku: str, price: float):
    if type(sku) != str:
        print('Variable sku must be of type str.')
        raise TypeError
    elif type(price) != float:
        print('Variable price must be of type float.')
        raise TypeError
    else:
        product = {
            'product': {
                'sku': sku,
                'price': price,
            },
            'saveOptions': True
        }
        return requests.post(url=f'{MAGENTO_API_URL}products', headers=headers, data=json.dumps(product), auth=auth)


def post_product_quantity(auth, sku: str, qty: int):
    if type(sku) != str:
        print('Variable sku must be of type str.')
        raise TypeError
    elif type(qty) != int:
        print('Variable qty must be of type int.')
        raise TypeError
    else:
        product = {
            'product': {
                'sku': sku,
                'extension_attributes': {
                    'stock_item': {
                        'qty': qty
                        }
                }
            },
            'saveOptions': True
        }
        return requests.post(url=f'{MAGENTO_API_URL}products', headers=headers, data=json.dumps(product), auth=auth)


def post_attribute_set(auth, attribute_set_name: str, sort_order: int, skeleton_id: int = 4, attribute_set_id: int = None, entity_type_id: int = None):
    if type(attribute_set_name) != str:
        print('Variable attribute_set_name must be of type str.')
        raise TypeError
    elif type(sort_order) != int:
        print('Variable sort_order must be of type int.')
        raise TypeError
    elif type(skeleton_id) != int:
        print('Optional variable skeleton_id must be of type int. Default is 4.')
        raise TypeError
    elif attribute_set_id is not None and type(attribute_set_id) != int:
        print('Optional variable attribute_set_id must be of type int.')
        raise TypeError
    elif entity_type_id is not None and type(entity_type_id) != int:
        print('Optional variable entity_type_id must be of type int.')
        raise TypeError
    else:
        attribute_set = {
            "attributeSet":
                {
                    "attribute_set_name": attribute_set_name,
                    "sort_order": sort_order,
                    "extension_attributes": {}
                },
            "skeletonId": skeleton_id
        }
        if attribute_set_id:
            attribute_set['attributeSet']['attribute_set_id'] = attribute_set_id
        if entity_type_id:
            attribute_set['attributeSet']['entity_type_id'] = entity_type_id
        return requests.post(url=f'{MAGENTO_API_URL}products/attribute-sets', headers=headers, data=json.dumps(attribute_set), auth=auth)


def post_attribute(auth, attribute_id: int, attribute_code: str, frontend_input: str, default_frontend_label: str, entity_type_id: str = 'text', is_required: bool = False,
                   is_pagebuilder_enabled: bool = False):
    if type(attribute_id) != int:
        print('Variable attribute_id must be of type int.')
        raise TypeError
    elif type(attribute_code) != str:
        print('Variable attribute_code must be of type str.')
        raise TypeError
    elif type(frontend_input) != str:
        print('Variable frontend_input must be of type str.')
        raise TypeError
    elif type(default_frontend_label) != str:
        print('Variable default_frontend_label must be of type str.')
        raise TypeError
    elif entity_type_id is not None and type(entity_type_id) != str:
        print('Optional variable entity_type_id must be of type str. Default is "text".')
        raise TypeError
    elif is_required is not None and type(is_required) != bool:
        print('Optional variable is_required must be of type bool. Default is False.')
        raise TypeError
    elif is_pagebuilder_enabled is not None and type(is_pagebuilder_enabled) != bool:
        print('Optional variable is_pagebuilder_enabled must be of type bool. Default is False.')
        raise TypeError
    else:
        attribute = {
            "attribute": {
                "attribute_id": attribute_id,
                "attribute_code": attribute_code,
                "frontend_input": frontend_input,
                "entity_type_id": default_frontend_label,
                "is_required": entity_type_id,
                "default_frontend_label": is_required,
                "extension_attributes": {
                    "is_pagebuilder_enabled": is_pagebuilder_enabled
                },
            }
        }
        return requests.post(url=f'{MAGENTO_API_URL}products/attributes', headers=headers, data=json.dumps(attribute), auth=auth)


def post_attribute_to_set(auth, attribute_set_id: int, attribute_group_id: int, attribute_code: str, sort_order: int):
    if type(attribute_set_id) != int:
        print('Variable attribute_set_id must be of type int.')
        raise TypeError
    elif type(attribute_group_id) != int:
        print('Variable attribute_group_id must be of type int.')
        raise TypeError
    elif type(attribute_code) != str:
        print('Variable attribute_code must be of type str.')
        raise TypeError
    elif type(sort_order) != int:
        print('Variable sort_order must be of type int.')
        raise TypeError
    else:
        link = {
            "attributeSetId": attribute_set_id,
            "attributeGroupId": attribute_group_id,
            "attributeCode": attribute_code,
            "sortOrder": sort_order
        }
        return requests.post(url=f'{MAGENTO_API_URL}products/attribute-sets/attributes', headers=headers, data=json.dumps(link), auth=auth)


def post_attribute_group(auth, attribute_group_id: str, attribute_group_name: str, attribute_set_id: int):
    if type(attribute_group_id) != str:
        print('Variable attribute_group_id must be of type str.')
        raise TypeError
    elif type(attribute_group_name) != str:
        print('Variable attribute_group_name must be of type str.')
        raise TypeError
    elif type(attribute_set_id) != int:
        print('Variable attribute_set_id must be of type int.')
        raise TypeError
    else:
        group = {
            "group":
                {
                    "attribute_group_id": attribute_group_id,
                    "attribute_group_name": attribute_group_name,
                    "attribute_set_id": attribute_set_id
                }
        }
        return requests.post(url=f'{MAGENTO_API_URL}products/attribute-sets/groups', headers=headers, data=json.dumps(group), auth=auth)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ORDER                                                                                                                                                                                          ORDER #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_pending_orders(auth):
    query = {'searchCriteria':
        {
            'filterGroups':
                [
                    {'filters':
                        [
                            {
                                'field': 'status',
                                'value': 'processing,pending',
                                'condition_type': 'in'
                            }
                        ]
                    }
                ]
        }
    }
    return requests.get(url=f'{MAGENTO_API_URL}orders', headers=headers, params=query, auth=auth)


def post_order_ready(auth, order_ids: int_list):
    if type(order_ids) != int_list:
        print('Variable order_ids must be a list of ints.')
        raise TypeError
    else:
        order_ids = {
            "orderIds": order_ids
        }
        return requests.post(url=f'{MAGENTO_API_URL}order/notify-orders-are-ready-for-pickup', headers=headers, data=json.dumps(order_ids), auth=auth)
