# -*- coding: utf-8 -*

from lotus import Marketplace_Product_Attributes
import afterbuy_api
from routines import ab_product_update

import xml.etree.ElementTree as ETree
from datetime import datetime, timedelta


order_update = []
stock_update = {}
product_ids = []
r = afterbuy_api.get_sold_items({'DateFilter': ['AuctionEndDate', (datetime.now()-timedelta(hours=6)).strftime('%d.%m.%Y %H:%M:%S'), (datetime.now()-timedelta(hours=0)).strftime('%d.%m.%Y %H:%M:%S')]})
tree = ETree.fromstring(r.text)
orders = tree.findall('.//Order')
for o in orders:
    order_id = o.find('.//OrderID')
    if order_id is None:
        print('Order-ID not found.')
        continue
    sold_items = o.findall('.//SoldItem')
    for sold_item in sold_items:
        p_id = sold_item.find('.//ProductID')
        if p_id is None:
            if len(sold_items) <= 1:
                anr = sold_item.find('.//Anr')
                if anr is None:
                    print(f'Anr for order {order_id.text} not found.')
                    continue
                quantity = sold_item.find('.//ItemQuantity')
                if quantity is None:
                    print(f'No Quantity for order {order_id.text} and Anr {anr.text} not found.')
                    continue
                mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_system_id=anr.text).first()
                if mpa is None:
                    print(f'Marketplace-Offer for order {anr.text} not found.')
                    continue
                product_ids.append(mpa.product_id)
                order_update.append({'order_id': order_id.text, 'item_id': anr.text, 'product_id': mpa.product.internal_id})
                print(order_update)
                stock_update[mpa.product_id] = {'add_auction_quantity': -1 * int(quantity.text)}
            else:
                order_update.append({'order_id': order_id.text, 'tags': ['NACHBESSERN']})
                print(order_update)
if order_update:
    r = afterbuy_api.update_sold_items(order_update)
    print(r.text)
if stock_update and product_ids:
    r = ab_product_update(product_ids=product_ids, stock_update=stock_update)
    print(r.text)
