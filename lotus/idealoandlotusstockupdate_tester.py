# -*- coding: utf-8 -*-

from lotus import *
from functions import money_to_float
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from datetime import *
import math
import csv

start = datetime.now()

products = Product.query.order_by(Product.internal_id.desc()).all()

url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"

request_quant = 250

shop_id = '318578'

client_id = '54743bc2-5f71-4143-a52a-a9502dcf4587'
client_pw = 'D2;jS$lnL0Z5,'
header = {'Content-Type': 'application/x-www-form-urlencoded'}

marketplace = Marketplace.query.filter_by(name='Idealo').first()

product_ids = []
error_ids = []

msg = ''

no_internal_ids = []

i=1
while i*request_quant<len(products):
    print(i)
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <Request>
        <AfterbuyGlobal>
            <PartnerID><![CDATA[1000007048]]></PartnerID>
            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
            <UserID><![CDATA[Lotusicafe]]></UserID>
            <UserPassword><![CDATA[210676After251174]]></UserPassword>
            <CallName>GetShopProducts</CallName>
            <DetailLevel>12</DetailLevel>
            <ErrorLanguage>DE</ErrorLanguage>
        </AfterbuyGlobal>
        <MaxShopItems>"""+str(request_quant)+"""</MaxShopItems>
        <DataFilter>
        <Filter>
            <FilterName>ProductID</FilterName>
            <FilterValues>\n"""
    for product in products[(i-1)*request_quant:i*request_quant]:
        # noinspection PyComparisonWithNone
        if product.internal_id == None:
            no_internal_ids.append(product.id)
        else:
            product_ids.append(product.id)
            xml+= """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
    xml+= """</FilterValues>
    </Filter>
    </DataFilter>
    </Request>
    """
    headers = {'Content-Type': 'application/xml'}
    r = requests.get(url, data=xml, headers=headers)

    tree = ET.fromstring(r.text)

    product_query = [item for item in tree.iter() if item.tag == 'Product']

    auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,
                 auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})

    json_data = auth.json()
    for prod in product_query:
        prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
        quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
        price = [item.text for item in prod.iter() if item.tag == 'SellingPrice'][0]
        product = Product.query.filter_by(internal_id=prod_id).first()
        if not product:
            print('no_product')
            print(prod_id)
            print('----------------------')
        if product:
            if product.id in product_ids:
                product_ids.remove(product.id)
            mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=marketplace.id).first()
            data = None
            try:
                sku = prod_id
                if mpa.uploaded and (datetime.now()-mpa.upload_date).seconds > 18000:
                    idealo_upload = True

                    URL = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"

                    header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
                              'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}

                    s = requests.get(url=URL, headers=header)

                    data = s.json()
                    if int(quant) > 0:
                        if int(data['checkoutLimitPerPeriod']) <= 0:
                            msg += str(product.id) + '<br>'
                            msg += 'Echt-Bestand: '+ str(quant) + '<br>'
                            msg += 'Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']) + '<br>'
                            msg += '-----------------------<br>'
                    if int(quant)  == 0:
                        if int(data['checkoutLimitPerPeriod']) > 0:
                            msg += str(product.id) + '<br>'
                            msg += 'Echt-Bestand: '+ str(quant) + '<br>'
                            msg += 'Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']) + '<br>'
                            msg += '-----------------------<br>'
            except:
                if data:
                    if 'generalErrors' in data:
                        error_ids.append(product.id)
                    else:
                        msg += 'Unidentifiable Error for ' + '<br>'
                        msg += str(product.id) + '<br>'
                        msg += '-----------------------<br>'
    i+=1

print(i)
xml = """<?xml version="1.0" encoding="utf-8"?>
        <Request>
            <AfterbuyGlobal>
                <PartnerID><![CDATA[1000007048]]></PartnerID>
                <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                <UserID><![CDATA[Lotusicafe]]></UserID>
                <UserPassword><![CDATA[210676After251174]]></UserPassword>
                <CallName>GetShopProducts</CallName>
                <DetailLevel>12</DetailLevel>
                <ErrorLanguage>DE</ErrorLanguage>
            </AfterbuyGlobal>
            <MaxShopItems>""" + str(request_quant) + """</MaxShopItems>
            <DataFilter>
            <Filter>
                <FilterName>ProductID</FilterName>
                <FilterValues>"""
for product in products[(i - 1) * request_quant:]:
    # noinspection PyComparisonWithNone
    if product.internal_id == None:
        no_internal_ids.append(product.id)
    else:
        product_ids.append(product.id)
        xml+= """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
xml += """</FilterValues>
        </Filter>
        </DataFilter>
        </Request>
        """
headers = {'Content-Type': 'application/xml'}
r = requests.get(url, data=xml, headers=headers)

tree = ET.fromstring(r.text)

product_query = [item for item in tree.iter() if item.tag == 'Product']

auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,
                     auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})

json_data = auth.json()
for prod in product_query:
    prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
    quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
    product = Product.query.filter_by(internal_id=prod_id).first()
    if not product:
        print('no_product')
        print(prod_id)
        print('----------------------')
    if product:
        if product.id in product_ids:
            product_ids.remove(product.id)
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=marketplace.id).first()
        data = None
        try:
            sku = prod_id
            if mpa.uploaded:
                idealo_upload = True

                URL = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"

                header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
                          'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}

                s = requests.get(url=URL, headers=header)

                data = s.json()
                if int(quant) > 0:
                    if int(data['checkoutLimitPerPeriod']) <= 0:
                        msg += str(product.id) + '<br>'
                        msg += 'Echt-Bestand: '+ str(quant) + '<br>'
                        msg += 'Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']) + '<br>'
                        msg += '-----------------------<br>'
                if int(quant)  == 0:
                    if int(data['checkoutLimitPerPeriod']) > 0:
                        msg += str(product.id) + '<br>'
                        msg += 'Echt-Bestand: '+ str(quant) + '<br>'
                        msg += 'Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']) + '<br>'
                        msg += '-----------------------<br>'
        except:
            if data:
                if 'generalErrors' in data:
                    error_ids.append(product.id)
                else:
                    msg += 'Unidentifiable Error for ' + '<br>'
                    msg += str(product.id) + '<br>'
                    msg += '-----------------------<br>'
i += 1
print(msg)
print(product_ids)
if msg or product_ids or error_ids or no_internal_ids:
    if product_ids:
        msg += 'Folgende Produkt-IDs sind bei Afterbuy nicht gefunden worden:<br>'
        msg += str(product_ids) + '<br>'
    if (product_ids and error_ids) or (product_ids and no_internal_ids):
        msg += '-----------------------<br>'
    if error_ids:
        msg += 'Folgende Produkt-IDs sind bei Idealo nicht gefunden worden:<br>'
        msg += str(error_ids)
    if error_ids and no_internal_ids:
        msg += '-----------------------<br>'
    if no_internal_ids:
        msg += 'Die Produkte mit den folgenden Produkt-IDs haben keine Interne ID:<br>'
        msg += str(no_internal_ids)
    send_email('Idealo- und Lotus-Stock-Update', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)
