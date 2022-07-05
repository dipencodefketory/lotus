# -*- coding: utf-8 -*-

"""SHOPIFY API-CALLS"""

from lotus import env_vars_path

import requests
from dotenv import load_dotenv
import os


load_dotenv(env_vars_path)

base_url = f'https://{os.environ["SHOPIFY_KEY"]}:{os.environ["SHOPIFY_PW"]}@lotus-icafe.myshopify.com/admin/api/2021-10'
headers = {'Content-Type': 'application/json'}


#*****************************************************************************************************************************************************************************************************#
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ORDERS                                                                                                                                                                                       ORDERS #
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#*****************************************************************************************************************************************************************************************************#

def cancel_order(order_id: str):
    if order_id is not None and type(order_id) != str:
        raise TypeError(f'Variable order_id must be of type str. {type(order_id)} given.')
    return requests.post(f'{base_url}orders/{order_id}/cancel.json', headers=headers)


def close_order(order_id: str):
    if order_id is not None and type(order_id) != str:
        raise TypeError(f'Variable order_id must be of type str. {type(order_id)} given.')
    return requests.post(f'{base_url}orders/{order_id}/close.json', headers=headers)


def reopen_order(order_id: str):
    if order_id is not None and type(order_id) != str:
        raise TypeError(f'Variable order_id must be of type str. {type(order_id)} given.')
    return requests.post(f'{base_url}orders/{order_id}/open.json', headers=headers)


def get_orders(created_at_min: str = None, created_at_max: str = None, financial_status: str = None, fulfillment_status: str = None, limit: int = None, processed_at_min: str = None,
               processed_at_max: str = None, status: str = None, updated_at_min: str = None, updated_at_max: str = None):
    if created_at_min is not None and type(created_at_min) != str:
        raise TypeError(f'Variable created_at_min must be of type str. {type(created_at_min)} given.')
    if created_at_max is not None and type(created_at_max) != str:
        raise TypeError(f'Variable created_at_max must be of type str. {type(created_at_max)} given.')
    if financial_status is not None and type(financial_status) != str:
        raise TypeError(f'Variable financial_status must be of type str. {type(financial_status)} given.')
    if fulfillment_status is not None and type(fulfillment_status) != str:
        raise TypeError(f'Variable fulfillment_status must be of type str. {type(fulfillment_status)} given.')
    if limit is not None and type(limit) != int:
        raise TypeError(f'Variable limit must be of type int. {type(int)} given.')
    if processed_at_min is not None and type(processed_at_min) != str:
        raise TypeError(f'Variable processed_at_min must be of type str. {type(processed_at_min)} given.')
    if processed_at_max is not None and type(processed_at_max) != str:
        raise TypeError(f'Variable processed_at_max must be of type str. {type(processed_at_max)} given.')
    if status is not None and type(status) != str:
        raise TypeError(f'Variable status must be of type str. {type(status)} given.')
    if updated_at_min is not None and type(updated_at_min) != str:
        raise TypeError(f'Variable updated_at_min must be of type str. {type(updated_at_min)} given.')
    if updated_at_max is not None and type(updated_at_max) != str:
        raise TypeError(f'Variable updated_at_max must be of type str. {type(updated_at_max)} given.')
    params = {}
    if created_at_min is not None:
        params['created_at_min'] = created_at_min
    if created_at_max is not None:
        params['created_at_max'] = created_at_max
    if financial_status is not None:
        params['financial_status'] = financial_status
    if fulfillment_status is not None:
        params['fulfillment_status'] = fulfillment_status
    if limit is not None:
        params['limit'] = limit
    if processed_at_min is not None:
        params['processed_at_min'] = processed_at_min
    if processed_at_max is not None:
        params['processed_at_max'] = processed_at_max
    if status is not None:
        params['status'] = status
    if updated_at_min is not None:
        params['updated_at_min'] = updated_at_min
    if updated_at_max is not None:
        params['updated_at_max'] = updated_at_max
    return requests.get(f'{base_url}/orders.json', headers=headers, params=params)


def get_order(order_id: str):
    if type(order_id) != str:
        raise TypeError(f'Variable order_id must be of type str. {type(order_id)} given.')
    return requests.get(f'{base_url}/orders/{order_id}.json', headers=headers)


#*****************************************************************************************************************************************************************************************************#
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# PRODUCTS                                                                                                                                                                                   PRODUCTS #
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#*****************************************************************************************************************************************************************************************************#

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# COLLECT                                                                                                                                                                                     COLLECT #
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def post_collect(collects: list):
    if type(collects) != list:
        raise TypeError(f'Variable collects must be of type list. {type(collects)} given.')
    if len(collects) == 0:
        raise ValueError(f'Variable collects must contain at least one element.')
    return requests.post(f'{base_url}/collects.json', headers=headers, data=collects)


def get_collects(product_id: str = None, collect_id: str = None):
    if product_id is not None and type(product_id) != str:
        raise TypeError(f'Variable product_id must be of type str. {type(product_id)} given.')
    if collect_id is not None and type(collect_id) != str:
        raise TypeError(f'Variable collect_id must be of type str. {type(collect_id)} given.')
    params = {}
    if product_id is not None:
        params['product_id'] = product_id
    if collect_id is not None:
        params['collect_id'] = collect_id
    return requests.get(f'{base_url}/collects.json', headers=headers, params=params)


def get_collect(collect_id: str):
    if type(collect_id) != str:
        raise TypeError(f'Variable collect_id must be of type str. {type(collect_id)} given.')
    return requests.get(f'{base_url}/collects/{collect_id}.json', headers=headers)


def del_collect(collect_id: str):
    if type(collect_id) != str:
        raise TypeError(f'Variable collect_id must be of type str. {type(collect_id)} given.')
    return requests.delete(f'{base_url}/collects/{collect_id}.json', headers=headers)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# CUSTOM_COLLECTION                                                                                                                                                                 CUSTOM_COLLECTION #
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def post_custom_collection(title: str, handle: str = None, body_html: str = None, image: str = None, published: bool = None, published_scope: str = None):
    if type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if handle is not None and type(handle) != str:
        raise TypeError(f'Variable handle must be of type str. {type(handle)} given.')
    if body_html is not None and type(body_html) != str:
        raise TypeError(f'Variable body_html must be of type str. {type(body_html)} given.')
    if image is not None and type(image) != str:
        raise TypeError(f'Variable image must be of type str. {type(image)} given.')
    if published is not None and type(published) != bool:
        raise TypeError(f'Variable published must be of type bool. {type(published)} given.')
    if published_scope is not None and type(published_scope) != str:
        raise TypeError(f'Variable published_scope must be of type str. {type(published_scope)} given.')
    custom_collection = {'title': title}
    if handle:
        custom_collection['handle'] = handle
    if body_html:
        custom_collection['body_html'] = body_html
    if image:
        custom_collection['image'] = image
    if published:
        custom_collection['published'] = published
    if published_scope:
        custom_collection['published_scope'] = published_scope
    data = {'custom_collection': custom_collection}
    return requests.post(f'{base_url}/custom_collections.json', headers=headers, json=data)


def get_custom_collections(handle: str = None, ids: list = None, product_id: str = None, published_at_min: str = None, published_at_max: str = None, published_status: str = None, title: str = None,
                        updated_at_min: str = None, updated_at_max: str = None):
    if handle is not None and type(handle) != str:
        raise TypeError(f'Variable handle must be of type str. {type(handle)} given.')
    if ids is not None and type(ids) != []:
        raise TypeError(f'Variable ids must be of type list. {type(ids)} given.')
    if product_id is not None and type(product_id) != str:
        raise TypeError(f'Variable product_id must be of type str. {type(product_id)} given.')
    if published_at_min is not None and type(published_at_min) != str:
        raise TypeError(f'Variable published_at_min must be of type str. {type(published_at_min)} given.')
    if published_at_max is not None and type(published_at_max) != str:
        raise TypeError(f'Variable published_at_max must be of type str. {type(published_at_max)} given.')
    if published_status is not None and type(published_status) != str:
        raise TypeError(f'Variable published_status must be of type str. {type(published_status)} given.')
    if title is not None and type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if updated_at_min is not None and type(updated_at_min) != str:
        raise TypeError(f'Variable updated_at_min must be of type str. {type(updated_at_min)} given.')
    if updated_at_max is not None and type(updated_at_max) != str:
        raise TypeError(f'Variable updated_at_max must be of type str. {type(updated_at_max)} given.')
    params = {}
    if handle is not None:
        params['handle'] = handle
    if ids is not None:
        params['ids'] = ids
    if product_id is not None:
        params['product_id'] = product_id
    if published_at_min is not None:
        params['published_at_min'] = published_at_min
    if published_at_max is not None:
        params['published_at_max'] = published_at_max
    if published_status is not None:
        params['published_status'] = published_status
    if title is not None:
        params['title'] = title
    if updated_at_min is not None:
        params['updated_at_min'] = updated_at_min
    if updated_at_max is not None:
        params['updated_at_max'] = updated_at_max
    return requests.get(f'{base_url}/custom_collections.json', headers=headers, params=params)


def get_custom_collection(custom_collection_id: str):
    if type(custom_collection_id) != str:
        raise TypeError(f'Variable custom_collection_id must be of type str. {type(custom_collection_id)} given.')
    return requests.get(f'{base_url}/custom_collections/{custom_collection_id}.json', headers=headers)


def put_custom_collection(custom_collection_id: str, title: str = None, handle: str = None, body_html: str = None, image: str = None, published: bool = None, published_scope: str = None):
    if type(custom_collection_id) != str:
        raise TypeError(f'Variable custom_collection_id must be of custom_collection_id str. {type(title)} given.')
    if title is not None and type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if handle is not None and type(handle) != str:
        raise TypeError(f'Variable handle must be of type str. {type(handle)} given.')
    if body_html is not None and type(body_html) != str:
        raise TypeError(f'Variable body_html must be of type str. {type(body_html)} given.')
    if image is not None and type(image) != str:
        raise TypeError(f'Variable image must be of type str. {type(image)} given.')
    if published is not None and type(published) != bool:
        raise TypeError(f'Variable published must be of type bool. {type(published)} given.')
    if published_scope is not None and type(published_scope) != str:
        raise TypeError(f'Variable published_scope must be of type str. {type(published_scope)} given.')
    custom_collection = {'id': custom_collection_id}
    if handle:
        custom_collection['title'] = title
    if handle:
        custom_collection['handle'] = handle
    if body_html:
        custom_collection['body_html'] = body_html
    if image:
        custom_collection['image'] = image
    if published:
        custom_collection['published'] = published
    if published_scope:
        custom_collection['published_scope'] = published_scope
    data = {'custom_collection': custom_collection}
    return requests.post(f'{base_url}/custom_collections/{custom_collection_id}.json', headers=headers, json=data)


def del_custom_collection(custom_collection_id: str):
    if type(custom_collection_id) != str:
        raise TypeError(f'Variable custom_collection_id must be of type str. {type(custom_collection_id)} given.')
    return requests.delete(f'{base_url}/custom_collections/{custom_collection_id}.json', headers=headers)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# PRODUCT                                                                                                                                                                                     PRODUCT #
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def post_product(body_html: str, title: str, images: list, category_name: str, ean: str, quantity: int, price: float, sku: str, weight: float, tags: list = None):
    if type(body_html) != str:
        raise TypeError(f'Variable body_html must be of type str. {type(body_html)} given.')
    if type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if type(images) != list:
        raise TypeError(f'Variable images must be of type list. {type(images)} given.')
    if type(category_name) != str:
        raise TypeError(f'Variable category_name must be of type str. {type(category_name)} given.')
    if type(ean) != str:
        raise TypeError(f'Variable ean must be of type str. {type(ean)} given.')
    if type(quantity) != int:
        raise TypeError(f'Variable quantity must be of type int. {type(quantity)} given.')
    if type(price) != float:
        raise TypeError(f'Variable price must be of type float. {type(price)} given.')
    if type(sku) != str:
        raise TypeError(f'Variable sku must be of type str. {type(sku)} given.')
    if type(weight) != float:
        raise TypeError(f'Variable weight must be of type float. {type(weight)} given.')
    if tags != None and type(tags) != list:
        raise TypeError(f'Variable tags must be of type list. {type(tags)} given.')
    data = {
        "product": {
            "body_html": body_html,
            "handle": title,
            "images": [{'src': img} for img in images],
            "product_type": category_name,
            "title": title,
            "variants": [
                {
                    "barcode": ean,
                    "inventory_quantity": quantity,
                    "position": 1,
                    "price": price,
                    "sku": sku,
                    "weight": weight,
                    "weight_unit": 'kg',
                }
            ]
        }
    }
    if tags is not None:
        data['tags'] = tags
    print(data)
    return requests.post(f'{base_url}/products.json', headers=headers, json=data)


def get_products(collection_id: str = None, created_at_min: str = None, created_at_max: str = None, handle: str = None, ids: list = None, presentment_currencies: str = None, product_type: str = None,
                 published_at_min: str = None, published_at_max: str = None, published_status: str = None, status: str = None, title: str = None, updated_at_min: str = None,
                 updated_at_max: str = None):
    if collection_id is not None and type(collection_id) != str:
        raise TypeError(f'Variable collection_id must be of type str. {type(collection_id)} given.')
    if created_at_min is not None and type(created_at_min) != str:
        raise TypeError(f'Variable created_at_min must be of type str. {type(created_at_min)} given.')
    if created_at_max is not None and type(created_at_max) != str:
        raise TypeError(f'Variable created_at_max must be of type str. {type(created_at_max)} given.')
    if handle is not None and type(handle) != str:
        raise TypeError(f'Variable handle must be of type str. {type(handle)} given.')
    if ids is not None and type(ids) != list:
        raise TypeError(f'Variable ids must be of type list. {type(ids)} given.')
    if presentment_currencies is not None and type(presentment_currencies) != str:
        raise TypeError(f'Variable presentment_currencies must be of type str. {type(presentment_currencies)} given.')
    if product_type is not None and type(product_type) != str:
        raise TypeError(f'Variable product_type must be of type str. {type(product_type)} given.')
    if published_at_min is not None and type(published_at_min) != str:
        raise TypeError(f'Variable published_at_min must be of type str. {type(published_at_min)} given.')
    if published_at_max is not None and type(published_at_max) != str:
        raise TypeError(f'Variable published_at_max must be of type str. {type(published_at_max)} given.')
    if published_status is not None and type(published_status) != str:
        raise TypeError(f'Variable published_status must be of type str. {type(published_status)} given.')
    if status is not None and type(status) != str:
        raise TypeError(f'Variable status must be of type str. {type(status)} given.')
    if title is not None and type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if updated_at_min is not None and type(updated_at_min) != str:
        raise TypeError(f'Variable updated_at_min must be of type str. {type(updated_at_min)} given.')
    if updated_at_max is not None and type(updated_at_max) != str:
        raise TypeError(f'Variable updated_at_max must be of type str. {type(updated_at_max)} given.')
    params = {}
    if collection_id is not None:
        params['collection_id'] = collection_id
    if created_at_min is not None:
        params['created_at_min'] = created_at_min
    if created_at_max is not None:
        params['created_at_max'] = created_at_max
    if handle is not None:
        params['handle'] = handle
    if ids is not None:
        params['ids'] = ids
    if presentment_currencies is not None:
        params['presentment_currencies'] = presentment_currencies
    if product_type is not None:
        params['product_type'] = product_type
    if published_at_min is not None:
        params['published_at_min'] = published_at_min
    if published_at_max is not None:
        params['published_at_max'] = published_at_max
    if published_status is not None:
        params['published_status'] = published_status
    if status is not None:
        params['status'] = status
    if title is not None:
        params['title'] = title
    if updated_at_min is not None:
        params['updated_at_min'] = updated_at_min
    if updated_at_max is not None:
        params['updated_at_max'] = updated_at_max
    return requests.get(f'{base_url}/products.json', headers=headers, params=params)


def get_product(product_id: str):
    if type(product_id) != str:
        raise TypeError(f'Variable product_id must be of type str. {type(product_id)} given.')
    return requests.get(f'{base_url}/products/{product_id}.json', headers=headers)


def put_product(product_id: str, body_html: str = None, title: str = None, images: list = None, category_name: str = None, ean: str = None, quantity: int = None, price: float = None, sku: str = None,
                weight: float = None, tags: list = None):
    if type(product_id) != str:
        raise TypeError(f'Variable product_id must be of type str. {type(product_id)} given.')
    if body_html is not None and type(body_html) != str:
        raise TypeError(f'Variable body_html must be of type str. {type(body_html)} given.')
    if title is not None and type(title) != str:
        raise TypeError(f'Variable title must be of type str. {type(title)} given.')
    if images is not None and type(images) != list:
        raise TypeError(f'Variable images must be of type list. {type(images)} given.')
    if category_name is not None and type(category_name) != str:
        raise TypeError(f'Variable category_name must be of type str. {type(category_name)} given.')
    if ean is not None and type(ean) != str:
        raise TypeError(f'Variable ean must be of type str. {type(ean)} given.')
    if quantity is not None and type(quantity) != int:
        raise TypeError(f'Variable quantity must be of type int. {type(quantity)} given.')
    if price is not None and type(price) != float:
        raise TypeError(f'Variable price must be of type float. {type(price)} given.')
    if sku is not None and type(sku) != str:
        raise TypeError(f'Variable sku must be of type str. {type(sku)} given.')
    if weight is not None and type(weight) != float:
        raise TypeError(f'Variable weight must be of type float. {type(weight)} given.')
    if tags is not None and type(tags) != list:
        raise TypeError(f'Variable tags must be of type list. {type(tags)} given.')
    product = {'id': product_id}
    if body_html is not None:
        product['body_html'] = body_html
    if title is not None:
        product['title'] = title
    if images is not None:
        product['images'] = [{'src': img} for img in images]
    if category_name is not None:
        product['category_name'] = category_name
    if ean or quantity or price or sku or weight:
        variants = {}
        if ean is not None:
            variants['ean'] = ean
        if quantity is not None:
            variants['quantity'] = quantity
        if price is not None:
            variants['price'] = price
        if sku is not None:
            variants['sku'] = sku
        if weight is not None:
            variants['weight'] = weight
        product['variants'] = [variants]
    if tags is not None:
        product['tags'] = tags
    print(product)
    return requests.put(f'{base_url}/products/{product_id}.json', headers=headers, json={'product': product})


def del_product(product_id: str):
    if type(product_id) != str:
        raise TypeError(f'Variable product_id must be of type str. {type(product_id)} given.')
    return requests.delete(f'{base_url}/products/{product_id}.json', headers=headers)
