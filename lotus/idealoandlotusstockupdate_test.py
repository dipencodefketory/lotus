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

i=1
while i*request_quant<len(products):
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
                if mpa.uploaded:
                    idealo_upload = True

                    URL = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"

                    header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
                              'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}

                    s = requests.get(url=URL, headers=header)

                    data = s.json()
                    if int(quant) > 0:
                        if int(data['checkoutLimitPerPeriod']) <= 0:
                            print('Echt-Bestand: '+ str(int(quant)))
                            print('Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']))
                            print(product.id)
                            print('-----------------------')
                    if int(quant)  == 0:
                        if int(data['checkoutLimitPerPeriod']) > 0:
                            print('Echt-Bestand: '+ str(int(quant)))
                            print('Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']))
                            print(product.id)
                            print('-----------------------')
            except:
                print('exception')
                if data:
                    print(data)
                print('-----------------------')
    i+=1

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
                <FilterValues>\n"""
for product in products[(i - 1) * request_quant:]:
    product_ids.append(product.id)
    xml += """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
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
                        print('Echt-Bestand: '+ str(int(quant)))
                        print('Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']))
                        print(product.id)
                        print('-----------------------')
                if int(quant)  == 0:
                    if int(data['checkoutLimitPerPeriod']) > 0:
                        print('Echt-Bestand: '+ str(int(quant)))
                        print('Idealo-Bestand: ' + str(data['checkoutLimitPerPeriod']))
                        print(product.id)
                        print('-----------------------')
        except:
            print('exception')
            if data:
                print(data)
            print('-----------------------')
i += 1
print(product_ids)