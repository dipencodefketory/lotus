# -*- coding: utf-8 -*-

import requests

# GLOBAL VARIABLES
token = '27b9782a5ef2213d8b2a4ed07289659e93374c9c'
base_url = 'https://dropship.entertainment-trading.com/api/'


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# ORDERS                                                                                                                                                                                        ORDERS #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_orders(page: int = 1, updated_since: str = '2020-01-01T00:00:00'):
    """
    :param page: integer in {1, 2, ...}
    :param updated_since: string of format YYYY-MM-DDTHH:MM:SS e.g. 2020-01-01T00:00:00
    :return: response containing dictionary of the general form
        {"count": 0, "next": "/api/orders/?page=3", "previous": "/api/orders/?page=1", "results":
            [
                {"id": 1, "status": "OPEN", "order_number": 1, "currency": "str", "phone": "string", "email": "user@example.com", "shipping_address":
                    {"name": "string", "attention": "string", "street": "string", "postcode": "string", "city": "string", "country": "dk"},
                "lines":
                    [
                        {"sku": "string", "title": "string", "qty": 1, "price_ex_vat": 0.01, "status": "OPEN", "deliveries":
                            [
                                {"id": 1, "created_at": "2019-08-24T14:15:22Z", "qty": 1, "tracking_number": "string"}
                            ]
                        }
                    ],
                "shipment_type": "string", "pickup_point": "string", "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z"
                }
            ]
        }
        if successful (200), else
        500 - internal server error
    """
    r = requests.get(f'{base_url}orders/', headers={'Authorization': f'Token {token}'}, params={'page': page, 'updated_since': updated_since})
    return r


def create_order(order_number: int, currency: str, phone: str, email: str, name: str, attention: str, street: str, postcode: str, city: str, country: str, lines: list, shipment_type: str,
                 pickup_point: str = None):
    """
    :param order_number: int32 - own unique order-id
    :param currency: str ISO-4217 currency code
    :param phone: str
    :param email: str
    :param name: str
    :param attention: str
    :param street: str
    :param postcode: str
    :param city: str
    :param country: str (ISO 3166-1 alpha-2)
    :param lines: list of dictionaries of the general form
        {"sku": "string", "title": "string", "qty": 1, "price_ex_vat": 0.01, "deliveries":
            [
                {
                    "qty": 1, "tracking_number": "string"
                }
            ]
        }
    :param shipment_type: str - one of the predefined shipping types
    :param pickup_point: str - optional
    :return: response containing dictionary of the genral form
        {"id": 1, "status": "OPEN", "order_number": 1, "currency": "str", "phone": "string", "email": "user@example.com", "shipping_address":
            {"name": "string", "attention": "string", "street": "string", "postcode": "string", "city": "string", "country": "dk"},
        "lines":
            [
                {"sku": "string", "title": "string", "qty": 1, "price_ex_vat": 0.01, "status": "OPEN", "deliveries":
                    [
                        {"id": 1, "created_at": "2019-08-24T14:15:22Z", "qty": 1, "tracking_number": "string"}
                    ]
                }
            ],
        "shipment_type": "string",
        "pickup_point": "string",
        "created_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z"
        }
        if successful (201), else
        400 - validation error
        500 - internal server error
    """
    order = {
        "order_number": order_number,
        "currency": currency,
        "phone": phone,
        "email": email,
        "shipping_address":
            {
                "name": name,
                "attention": attention,
                "street": street,
                "postcode": postcode,
                "city": city,
                "country": country
            },
        "lines": lines,
        "shipment_type": shipment_type
    }
    if pickup_point:
        order["pickup_point"] = pickup_point
    r = requests.post(f'{base_url}orders/', headers={'Authorization': f'Token {token}', 'Content-Type': 'application/json; charset=UTF-8'}, json=order)
    return r


def get_order(order_id: int):
    """
    :param order_id: int32 as given by Entertainment-Trading
    :return: response containing dictionary of the general form
        {"id": 1, "status": "OPEN", "order_number": 1, "currency": "str", "phone": "string", "email": "user@example.com", "shipping_address":
            {"name": "string", "attention": "string", "street": "string", "postcode": "string", "city": "string", "country": "dk"},
        "lines":
            [
                {"sku": "string", "title": "string", "qty": 1, "price_ex_vat": 0.01, "status": "OPEN", "deliveries":
                        [
                            {
                                "id": 1, "created_at": "2019-08-24T14:15:22Z", "qty": 1, "tracking_number": "string"
                            }
                        ]
                }
            ],
        "shipment_type": "string", "pickup_point": "string", "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z"}
        if successful (200), else
        404 - not found
        500 - internal server error
    """
    r = requests.post(f'{base_url}orders/{order_id}', headers={'Authorization': f'Token {token}'})
    return r


def cancel_order(order_id: int, lines: list = None):
    """
    Starts the process. Status of order can be tracked via order change status request.
    :param order_id: int32 as given by Entertainment-Trading
    :param lines: list of dictionaries of the form {'sku': sku} for items to be cancelled
    :return: response containing dictionary of the general form
        {"id": 1, "order": 1, "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z", "change_type": "CANCELLATION", "status": "PENDING"}
        if successful (201), else
        400 - validation error
        404 - not found
        409 - not cancellable
        500 - internal server error
    """
    if lines:
        data = {
            "lines": lines
        }
    else:
        data = {
            "lines": []
        }
    r = requests.post(f'{base_url}orders/{order_id}/cancel/', headers={'Authorization': f'Token {token}'}, json=data)
    return r


def change_order_address(order_id: int, name: str, attention: str, street: str, postcode: str, city: str, country: str):
    """
    Starts the process. Status of order can be tracked via order change status request.
    :param order_id: int32 as given by Entertainment-Trading
    :param name: str
    :param attention: str
    :param street: str
    :param postcode: str
    :param city: str
    :param country: str (ISO 3166-1 alpha-2)
    :return: response containing dictionary of the general form
        {"id": 1, "order": 1, "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z", "change_type": "CANCELLATION", "status": "PENDING"}
        if successful (201), else
        400 - validation error
        404 - not found
        409 - not changeable
        500 - internal server error
    """
    data = {"name": name, "attention": attention, "street": street, "postcode": postcode, "city": city, "country": country}
    r = requests.post(f'{base_url}orders/{order_id}/change-address/', headers={'Authorization': f'Token {token}'}, json=data)
    return r


def get_order_change_requests(order_id: int):
    """
    :param order_id: int32 as given by Entertainment-Trading
    :return: response containing dictionary of the general form
        {"count": 0, "next": "/api/orders/1/change-requests/?page=3", "previous": "/api/orders/1/change-requests/?page=1", "results":
            [
                {"id": 1, "order": 1, "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z", "change_type": "CANCELLATION", "status": "PENDING"}
            ]
        }
        if successful (200), else
        404 - not found
        500 - internal server error
    """
    r = requests.get(f'{base_url}orders/{order_id}/change-requests/', headers={'Authorization': f'Token {token}'})
    return r


def get_order_change_request(change_request_id: int):
    """
    :param change_request_id: int32 as given by Entertainment-Trading
    :return: response containing dictionary of the general form
        {"id": 1, "order": 1, "created_at": "2019-08-24T14:15:22Z", "updated_at": "2019-08-24T14:15:22Z", "change_type": "CANCELLATION", "status": "PENDING"}
        if successful (200), else
        404 - not found
        500 - internal server error
    """
    r = requests.get(f'{base_url}order-change-requests/{change_request_id}/', headers={'Authorization': f'Token {token}'})
    return r


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# DELIVERIES                                                                                                                                                                                DELIVERIES #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_deliveries(page: int = 1, updated_since: str = '2020-01-01T00:00:00'):
    """
    :param page: integer in {1, 2, ...}
    :param updated_since: string of format YYYY-MM-DDTHH:MM:SS e.g. 2020-01-01T00:00:00
    :return: response containing dictionary of the general form
        {"count": 0, "next": "/api/deliveries/?page=3", "previous": "/api/deliveries/?page=1", "results":
            [
                {"id": 1, "doc_num": 1, "tracking_number": "string", "order_id": 1, "created_at": "2019-08-24T14:15:22Z", "lines":
                    [
                        {"sku": "string", "title": "string", "qty": 1}
                    ]
                }
            ]
        }
        if successful (200), else
        500 - internal server error
    """
    r = requests.get(f'{base_url}deliveries/', headers={'Authorization': f'Token {token}'}, params={'page': page, 'updated_since': updated_since})
    return r


def get_delivery(delivery_id: int):
    """
    :param delivery_id: int32 as given by Entertainment-Trading
    :return: response containing dictionary of the general form
        {"id": 1, "doc_num": 1, "tracking_number": "string", "order_id": 1, "created_at": "2019-08-24T14:15:22Z", "lines":
            [
                {"sku": "string", "title": "string", "qty": 1}
            ]
        }
        if successful (200), else
        404 - not found
        500 - internal server error
    """
    r = requests.post(f'{base_url}deliveries/{delivery_id}', headers={'Authorization': f'Token {token}'})
    return r


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# INVOICES                                                                                                                                                                                    INVOICES #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_invoices(page: int = 1, updated_since: str = '2020-01-01T00:00:00'):
    """
    :param page: integer in {1, 2, ...}
    :param updated_since: string of format YYYY-MM-DDTHH:MM:SS e.g. 2020-01-01T00:00:00
    :return: response containing dictionary of the general form
        {"count": 0, "next": "/api/invoices/?page=3", "previous": "/api/invoices/?page=1", "results":
            [
                {"id": 1, "doc_num": 1, "order_id": 1, "created_at": "2019-08-24T14:15:22Z", "total_amount_ex_vat": 0.01, "total_vat": 0.01, "total_amount_incl_vat": 0.01, "vat_percent": 0, "lines":
                    [
                        {"sku": "string", "title": "string", "qty": 1, "unit_amount_ex_vat": 0.01, "unit_amount_incl_vat": 0.01, "unit_vat_amount": 0.01, "total_amount_ex_vat": 0.01,
                        "total_amount_incl_vat": 0.01, "total_vat": 0.01}
                    ]
                }
            ]
        }
        if successful (200), else
        500 - internal server error
    """
    r = requests.get(f'{base_url}invoices/', headers={'Authorization': f'Token {token}'}, params={'page': page, 'updated_since': updated_since})
    return r


def get_invoice(invoice_id: int):
    """
    :param invoice_id: int32 as given by Entertainment-Trading
    :return: response containing dictionary of the general form
        {"id": 1, "doc_num": 1, "order_id": 1, "created_at": "2019-08-24T14:15:22Z", "total_amount_ex_vat": 0.01, "total_vat": 0.01, "total_amount_incl_vat": 0.01, "vat_percent": 0, "lines":
            [
                {"sku": "string", "title": "string", "qty": 1, "unit_amount_ex_vat": 0.01, "unit_amount_incl_vat": 0.01, "unit_vat_amount": 0.01, "total_amount_ex_vat": 0.01,
                "total_amount_incl_vat": 0.01, "total_vat": 0.01}
            ]
        }
        if successful (200), else
        404 - not found
        500 - internal server error
    """
    r = requests.post(f'{base_url}invoices/{invoice_id}', headers={'Authorization': f'Token {token}'})
    return r
