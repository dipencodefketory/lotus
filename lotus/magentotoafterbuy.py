# -*- coding: utf-8 -*-

from lotus import Marketplace, Product
from magento_api import get_pending_orders, get_auth
from datetime import datetime
import csv
import requests
import json
import urllib

def and_for_and(string: str) -> str:
    return string.replace('&', 'und').replace('#', '').replace('?', '%3F').replace('=', '%3D')


auth = get_auth()
r = get_pending_orders(auth)
data = r.json()
orders = data['items']

start = datetime.now()

marketplace = Marketplace.query.filter_by(name='Idealo').first()

path = '/home/lotus/logs/magento_to_afterbuy/'

with open(path + start.strftime('%Y%m%d%H%M')+'.csv', 'w', newline='') as csvfile:
    first_row = ['order_id', 'req_response']
    spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(first_row)
    for order in orders:
        url = "https://api.afterbuy.de/afterbuy/ShopInterfaceUTF8.aspx?"
        order_dict = {'Action': 'new',
                      'PartnerID': 1000007048,
                      'PartnerPass': 'epK7Ob9QO1geo44zUHqrgPhnU',
                      'UserID': 'Lotusicafe',
                      'PosAnz': len(order['items']),
                      'Kbenutzername': order['customer_is_guest']*'Gast-'+order['customer_firstname']+order['customer_lastname'],
                      'KVorname': order['customer_firstname'],
                      'KNachname': order['customer_lastname'],
                      'KStrasse': order['billing_address']['street'],
                      'KStrasse2': '',     # Herausfinden, wo zu finden
                      'KPLZ': order['billing_address']['postcode'],
                      'KOrt': order['billing_address']['city'],
                      'Ktelefon': order['billing_address']['telephone'],
                      'Kemail': order['billing_address']['email'],
                      'KLand': order['billing_address']['country_id'],

                      }
        shipping_address = order['extension_attributes']['shipping_assignments'][0]['shipping']['address']
        if shipping_address['street'] != order['billing_address']['street'] and shipping_address['postcode'] != order['billing_address']['postcode']:
            update_dict = {'Lieferanschrift': 1,
                           'KLVorname': shipping_address['customer_firstname'],
                           'KLNachname': shipping_address['customer_lastname'],
                           'KLStrasse': shipping_address['street'],
                           'KStrasse2': '',     # Herausfinden, wo zu finden
                           'KLPLZ': shipping_address['postcode'],
                           'KLOrt': shipping_address['city'],
                           'KLLand': shipping_address['country_id'],
                           'KLTelefon': shipping_address['telephone']
            }
            order_dict.update(update_dict)
        else:
            order_dict['Lieferanschrift'] = 0
        i=1
        for item in order['items']:
            product = Product.query.filter_by(internal_id=item['sku']).first()

            created_at = datetime.strptime(item['created_at'][:19], '%Y-%m-%d %H:%M:%S')
            update_dict = {f'Artikelnr_{i}': item['sku'],
                           f'AlternArtikelNr1_{i}': item['sku'],
                           f'AlternArtikelNr2_{i}': order['increment_id'],
                           f'Artikelname_{i}': item['name'],
                           f'ArtikelEpreis_{i}': item['price'],
                           f'ArtikelMwSt_{i}': item['tax_percent'],
                           f'ArtikelMenge_{i}': item['qty_ordered'],
                           f'ArtikelStammID_{i}': item['sku']
                           }
            order_dict.update(update_dict)
            i+=1

        update_dict = {'BuyDate': order['created_at'],
                       'PayDate': order['created_at'],
                       'Versandkosten': order['payment']['base_shipping_amount'],
                       'VID': order['increment_id'],
                       'CheckVID': 1,
                       'Zahlart': order['payment']['method'],
                       'NoFeedback': 2,
                       'SoldCurrency': order['base_currency_code'],
                       'Kundenerkennung': 1,
                       'Artikelerkennung': 0,
                       'Bestandart': 'auktion'
                       }
        order_dict.update(update_dict)
        order_dict['SetPay'] = 0 if order['base_total_due'] > 0 else 1
        url += urllib.parse.urlencode(order_dict)
        print(url)
        r = requests.post(url)
        print(r.status_code)
        print(r.text)
        print('---------------')
        spamwriter.writerow([order['increment_id'], r.text])
    end = datetime.now()
    spamwriter.writerow(['start: ' + start.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['end: ' + end.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['runtime: ' + str((end - start).seconds) + ' seconds'])

data = []
