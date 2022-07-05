# -*- coding: utf-8 -*-

from lotus import *
import requests
from datetime import *
import csv
from idealo_order import get_access_token, get_orders


def and_for_and(string: str) -> str:
    return string.replace('&', 'und')


start = datetime.now()

info = []

URL = "https://checkout-api.idealo.com/v1/orders?key=f64c464dd65c4a969878"
r = requests.get(url=URL)
data = r.json()

marketplace = Marketplace.query.filter_by(name='Idealo').first()

path = '/home/lotus/logs/idealo_to_afterbuy/'
#path = ''

with open(path + start.strftime('%Y%m%d%H%M')+'.csv', 'w', newline='') as csvfile:
    first_row = ['order_id', 'req_response']
    spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(first_row)
    for order in data:
        url = "https://api.afterbuy.de/afterbuy/ShopInterfaceUTF8.aspx?Action=new&"
        url += 'Partnerid=1000007048&'
        url += 'PartnerPass=epK7Ob9QO1geo44zUHqrgPhnU&'
        url += 'UserID=Lotusicafe&'
        url += 'PosAnz='+ str(len(order['line_items'])) +'&'
        url += 'Kbenutzername='+ and_for_and(order['billing_address']['given_name']) + ' '+ and_for_and(order['billing_address']['family_name']) +'&'
        url += 'Kanrede='+ order['billing_address']['salutation'] +'&'
        url += 'KFirma=&'
        url += 'KVorname='+ and_for_and(order['billing_address']['given_name'].replace(' ', '+')) +'&'
        url += 'KNachname='+ and_for_and(order['billing_address']['family_name'].replace(' ', '+')) +'&'
        url += 'KStrasse='+ and_for_and(order['billing_address']['address1'].replace(' ', '+')) +'&'
        url += 'KStrasse2='+ and_for_and(order['billing_address']['address2'].replace(' ', '+')) +'&'
        url += 'KPLZ='+ and_for_and(order['billing_address']['zip'].replace(' ', '+')) +'&'
        url += 'KOrt='+ and_for_and(order['billing_address']['city'].replace(' ', '+')) +'&'
        try:
            url += 'Ktelefon='+ order['customer']['phone'].replace(' ', '+') +'&'
        except:
            url += 'Ktelefon=&'
        url += 'Kemail='+ and_for_and(order['customer']['email']) +'&'
        url += 'KLand='+ and_for_and(order['billing_address']['country']) +'&'
        url += 'KBirthday=&'
        if order['billing_address'] != order['shipping_address']:
            url += 'Lieferanschrift=1&'
            url += 'KLFirma=&'
            url += 'KLVorname=' + and_for_and(order['shipping_address']['given_name'].replace(' ', '+')) + '&'
            url += 'KLNachname=' + and_for_and(order['shipping_address']['family_name'].replace(' ', '+')) + '&'
            url += 'KLStrasse=' + and_for_and(order['shipping_address']['address1'].replace(' ', '+')) + '&'
            url += 'KLStrasse2=' + and_for_and(order['shipping_address']['address2'].replace(' ', '+')) + '&'
            url += 'KLPLZ=' + and_for_and(order['shipping_address']['zip'].replace(' ', '+')) + '&'
            url += 'KLOrt=' + and_for_and(order['shipping_address']['city'].replace(' ', '+')) + '&'
            url += 'KLLand=D&'
            try:
                url += 'KLTelefon='+ order['customer']['phone'].replace(' ', '+') +'&'
            except:
                url += 'KLTelefon=&'
        else:
            url += 'Lieferanschrift=0&'
        i=1
        for art in order['line_items']:
            product = Product.query.filter_by(internal_id=art['sku']).first()

            created_at = datetime.strptime(order['created_at'][:19], '%Y-%m-%dT%H:%M:%S')
            url += 'Artikelnr_'+ str(i) +'='+ art['sku'] +'&'
            url += 'AlternArtikelNr1_'+ str(i) + '=' + art['sku'] +'&'
            url += 'AlternArtikelNr2_'+ str(i) + '=' + order['order_number'] +'&'
            url += 'Artikelname_'+ str(i) + '=' + and_for_and(art['title'].replace(' ', '+')) +'&'
            url += 'ArtikelEpreis_'+ str(i) + '='+ art['item_price'].replace('.', ',') +'&'
            url += 'ArtikelMwSt_'+ str(i) + '=19&'
            url += 'ArtikelMenge_'+ str(i) + '=' + str(art['quantity']) + '&'
            url += 'ArtikelStammID_'+ str(i) + '=' + art['sku'] +'&'
            i+=1

        url += 'BuyDate='+ order['created_at'] +'&'
        url += 'PayDate='+ order['created_at'] +'&'

        url += 'Versandkosten='+ order['total_shipping'].replace('.', ',') +'&'
        url += 'VID='+ order['order_number'] +'&'
        url += 'CheckVID=1&'
        if order['payment']['payment_method'] == 'PAYPAL':
            url += 'ZFunktionsID=5&'
        else:
            url += 'ZFunktionsID=&'
        url += 'Zahlart='+ and_for_and(order['payment']['payment_method']) +'&'
        url += 'PaymentTransactionId='+ order['payment']['transaction_id'] +'&'
        url += 'PaymentStatus=Completed&'
        url += 'NoFeedback=2&'
        url += 'SoldCurrency='+ order['currency'] +'&'
        url += 'SetPay=1&'
        url += 'Kundenerkennung=1&'
        url += 'Artikelerkennung=0&'
        url += 'Bestandart=auktion'
        r = requests.post(url)
        print(order['order_number'])
        print('---------------')
        spamwriter.writerow([order['order_number'], r.text])
    end = datetime.now()
    spamwriter.writerow(['start: ' + start.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['end: ' + end.strftime('%d.%m.%Y - %H:%M:%S')])
    spamwriter.writerow(['runtime: ' + str((end - start).seconds) + ' seconds'])

data = []
