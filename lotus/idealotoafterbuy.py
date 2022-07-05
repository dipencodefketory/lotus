# -*- coding: utf-8 -*-

from lotus import *
import requests
from datetime import *
import csv
from idealo_order import get_access_token, get_orders


def and_for_and(string: str) -> str:
    return string.replace('&', 'und').replace('#', '').replace('?', '%3F').replace('=', '%3D')


start = datetime.now()

info = []

access_dict = get_access_token()
r = get_orders(access_dict)
data = r.json()
print(data)
orders = data['content']

i = 1
while i < data['totalPages']:
    r = get_orders(access_dict, page_number=i-1)
    data = r.json()
    orders += data['content']

p_length = len(orders)  # Number of orders being processed.

r = get_orders(access_dict, status=['REVOKING'])
data = r.json()
orders += data['content']
i = 1
while i < data['totalPages']:
    r = get_orders(access_dict, status=['REVOKING'], page_number=i-1)
    data = r.json()
    orders += data['content']

marketplace = Marketplace.query.filter_by(name='Idealo').first()

path = '/home/lotus/logs/idealo_to_afterbuy/'

with open(path + start.strftime('%Y%m%d%H%M')+'.csv', 'w', newline='') as csvfile:
    first_row = ['order_id', 'req_response']
    spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(first_row)
    for k, order in enumerate(orders):
        print(order)
        url = "https://api.afterbuy.de/afterbuy/ShopInterfaceUTF8.aspx?Action=new&"
        url += 'Partnerid=1000007048&'
        url += 'PartnerPass=epK7Ob9QO1geo44zUHqrgPhnU&'
        url += 'UserID=Lotusicafe&'
        url += 'PosAnz='+ str(len(order['lineItems'])) +'&'
        url += 'Kbenutzername='+ and_for_and(order['billingAddress']['firstName']) + ' ' + and_for_and(order['billingAddress']['lastName']) +'&'
        url += 'Kanrede='+ order['billingAddress']['salutation'] +'&'
        url += 'KFirma=&'
        url += 'KVorname='+ and_for_and(order['billingAddress']['firstName'].replace(' ', '+')) +'&'
        url += 'KNachname='+ and_for_and(order['billingAddress']['lastName'].replace(' ', '+')) +'&'
        url += 'KStrasse='+ and_for_and(order['billingAddress']['addressLine1'].replace(' ', '+')) +'&'
        if 'addressLine2' in order['billingAddress']:
            url += 'KStrasse2='+ and_for_and(order['billingAddress']['addressLine2'].replace(' ', '+')) +'&'
        url += 'KPLZ='+ and_for_and(order['billingAddress']['postalCode'].replace(' ', '+')) +'&'
        url += 'KOrt='+ and_for_and(order['billingAddress']['city'].replace(' ', '+')) +'&'
        try:
            url += 'Ktelefon='+ order['customer']['phone'].replace(' ', '+') +'&'
        except:
            url += 'Ktelefon=&'
        url += 'Kemail='+ and_for_and(order['customer']['email']) +'&'
        url += 'KLand='+ and_for_and(order['billingAddress']['countryCode']) +'&'
        url += 'KBirthday=&'
        if order['billingAddress'] != order['shippingAddress']:
            url += 'Lieferanschrift=1&'
            url += 'KLFirma=&'
            url += 'KLVorname=' + and_for_and(order['shippingAddress']['firstName'].replace(' ', '+')) + '&'
            url += 'KLNachname=' + and_for_and(order['shippingAddress']['lastName'].replace(' ', '+')) + '&'
            url += 'KLStrasse=' + and_for_and(order['shippingAddress']['addressLine1'].replace(' ', '+')) + '&'
            if 'addressLine2' in order['shippingAddress']:
                url += 'KStrasse2='+ and_for_and(order['shippingAddress']['addressLine2'].replace(' ', '+')) +'&'
            url += 'KLPLZ=' + and_for_and(order['shippingAddress']['postalCode'].replace(' ', '+')) + '&'
            url += 'KLOrt=' + and_for_and(order['shippingAddress']['city'].replace(' ', '+')) + '&'
            url += 'KLLand=D&'
            try:
                url += 'KLTelefon='+ order['customer']['phone'].replace(' ', '+') +'&'
            except:
                url += 'KLTelefon=&'
        else:
            url += 'Lieferanschrift=0&'
        i=1
        for line_item in order['lineItems']:
            product = Product.query.filter_by(internal_id=line_item['sku']).first()

            created_at = datetime.strptime(order['created'][:19], '%Y-%m-%dT%H:%M:%S')
            url += 'Artikelnr_'+ str(i) +'='+ line_item['sku'] +'&'
            url += 'AlternArtikelNr1_'+ str(i) + '=' + line_item['sku'] +'&'
            url += 'AlternArtikelNr2_'+ str(i) + '=' + order['idealoOrderId'] +'&'
            url += 'Artikelname_'+ str(i) + '=' + and_for_and(line_item['title'].replace(' ', '+')) +'&'
            url += 'ArtikelEpreis_'+ str(i) + '='+ line_item['price'].replace('.', ',') +'&'
            url += 'ArtikelMwSt_'+ str(i) + '=19&'
            url += 'ArtikelMenge_'+ str(i) + '=' + str(line_item['quantity']) + '&'
            url += 'ArtikelStammID_'+ str(i) + '=' + line_item['sku'] +'&'
            url += 'ArtikelTag_' + str(i) + f'_1=Idealo&'
            m = 2
            if product.short_sell and product.get_own_real_stock()<=0:
                url += 'ArtikelTag_' + str(i) + f'_{m}=LVK&'
                m += 1
            if product.release_date:
                if product.release_date > datetime.now():
                    url += 'ArtikelTag_' + str(i) + f'_{m}=PRE ORDER&'
                    m+=1
            if k >= p_length:
                url += 'ArtikelTag_'+ str(i) + f'_{m}=STORNO&'
                m += 1
            i+=1

        url += 'BuyDate='+ order['created'] +'&'
        url += 'PayDate='+ order['created'] +'&'

        url += 'Versandkosten='+ order['shippingCosts'].replace('.', ',') +'&'
        url += 'VID='+ order['idealoOrderId'] +'&'
        url += 'CheckVID=1&'
        if order['payment']['paymentMethod'] == 'PAYPAL':
            url += 'ZFunktionsID=5&'
        else:
            url += 'ZFunktionsID=&'
        url += 'Zahlart='+ and_for_and(order['payment']['paymentMethod']) +'&'
        url += 'PaymentTransactionId='+ order['payment']['transactionId'] +'&'
        url += 'PaymentStatus=Completed&'
        url += 'NoFeedback=2&'
        url += 'SoldCurrency='+ order['currency'] +'&'
        url += 'SetPay=1&'
        url += 'Kundenerkennung=1&'
        url += 'Artikelerkennung=0&'
        url += 'Bestandart=auktion'
        r = requests.post(url)
        print(order['idealoOrderId'])
        print(r.status_code)
        print('---------------')
        spamwriter.writerow([order['idealoOrderId'], r.text])
    end = datetime.now()
    spamwriter.writerow(['start: ' + start.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['end: ' + end.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['runtime: ' + str((end - start).seconds) + ' seconds'])

data = []
