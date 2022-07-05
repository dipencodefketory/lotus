# -*- coding: utf-8 -*-

from lotus import Product, Marketplace, Marketplace_Product_Attributes
import afterbuy_api

import xml.etree.ElementTree as ETree
from datetime import datetime, timedelta


orders = []
r = afterbuy_api.get_sold_items({'DateFilter': ['AuctionEndDate', (datetime.now()-timedelta(days=5)).strftime('%d.%m.%Y %H:%M:%S'), datetime.now().strftime('%d.%m.%Y %H:%M:%S')],
                                 'DefaultFilter': ['not_CompletedAuctions']})
tree = ETree.fromstring(r.text)
for order in tree.findall('.//Order'):
    platform = order.find('.//ItemPlatformName')
    if platform.text=='105168_lotusicafe':
        print('Idealo')
        marketplace = Marketplace.query.filter_by(name='Idealo').first()
    else:
        print('Ebay')
        marketplace = Marketplace.query.filter_by(name='Ebay').first()
    for item in order.findall('.//SoldItem'):
        internal_id = item.find('.//ProductID')
        if internal_id is not None:
            product = Product.query.filter_by(internal_id=internal_id.text).first()
        elif marketplace.name == 'Ebay':
            ebay_id = item.find('.//Anr')
            if ebay_id is not None:
                mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_system_id=ebay_id.text, marketplace_id=marketplace.id).first()
                if mpa is None:
                    print(f'No product found for Ebay-ID {ebay_id.text}.')
                    continue
                product = mpa.product
        tags = []
        if product.short_sell and product.get_own_real_stock() <= 0:
            tags.append('LVK')
        if product.release_date:
            if product.release_date > datetime.now():
                tags.append('PRE ORDER')
        if tags:
            orders.append({'order_id': order.findtext('OrderID'), 'tags': tags})
print(orders)
result = afterbuy_api.update_sold_items(orders)
print(result.status_code)
print(result.text)
