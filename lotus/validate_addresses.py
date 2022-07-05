#-*- coding: utf-8 -*-

import afterbuy_api
from other_apis import validate_address
from datetime import datetime, timedelta
import xml.etree.ElementTree as ETree


def correct_addresses(from_datetime: datetime, to_datetime: datetime):
    address_list = []
    for i in range((to_datetime-from_datetime).days+1):
        r = afterbuy_api.get_sold_items({'DateFilter': ['AuctionEndDate', (from_datetime+timedelta(days=i)).strftime('%d.%m.%Y %H:%M:%S'), (from_datetime+timedelta(days=i+1)).strftime('%d.%m.%Y %H:%M:%S')],
                            'DefaultFilter': 'CompletedAuctions'
                            })
        tree = ETree.fromstring(r.text)
        for item in tree.iter():
            if item.tag == 'Order':
                tracking_code = item.findtext('AdditionalInfo')
                shipping_info = item.find('ShippingInfo')
                shipping_method = shipping_info.findtext('ShippingMethod')
                if shipping_method in ['de_DHLPaket', 'DE_DHLPaket', 'DE_DHLAlterssichtprüfung18'] and not tracking_code:
                    buyer_info = item.find('BuyerInfo')
                    address_info = item.find('ShippingAddress')
                    if not address_info:
                        address_info = buyer_info.find('BillingAddress')
                    country_code = address_info.findtext('CountryISO')
                    street_address = address_info.findtext('Street')
                    additional_address_info = address_info.findtext('Street2')
                    postal_code = address_info.findtext('PostalCode')
                    city = address_info.findtext('City')
                    print(country_code)
                    print(street_address)
                    print(additional_address_info)
                    print(postal_code)
                    print(city)
                    r = validate_address({'CountryCode': country_code, 'StreetAddress': street_address, 'AdditionalAddressInfo': additional_address_info, 'City': postal_code, 'PostalCode': city})
                    data = r.json()
                    print(r.text)
                    if data['status'] in ['VALID', 'SUSPECT']:
                        if 'supplement' not in data:
                            data['supplement'] = ''
                        address_list.append({'order_id': item.findtext('OrderID'), 'status': data['status'],
                                             'country_code': (country_code, data['country']),
                                             'street_address': (street_address, f'{data["street"]} {data["streetnumber"]}'),
                                             'additional_address_info': (additional_address_info, data['supplement']),
                                             'postal_code': (postal_code, data['postalcode']),
                                             'city': (city, data['city'])})
                    else:
                        print(r.text)
    return address_list

