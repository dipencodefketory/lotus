# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Product_Stock_Attributes, Sale, StockUpdateQueue
import afterbuy_api

import xml.etree.ElementTree as ETree
from datetime import datetime


r = afterbuy_api.get_sold_items(filters={'Tag': [datetime.now().strftime('%d.%m.%y')]})
tree = ETree.fromstring(r.text)
orders = tree.findall('.//Order')
for order in orders:
    order_id = order.find('.//OrderID').text
    sold_items = order.findall('.//SoldItem')
    product_ids = {}
    for sold_item in sold_items:
        product_ids[sold_item.find('.//ProductID').text] = sold_item.find('.//ItemQuantity').text
    sales = Sale.query.filter_by(order_number=order_id).all()
    for sale in sales:
        if sale.pricinglog.product.internal_id in product_ids:
            product_ids.pop(sale.pricinglog.product.internal_id)
            sales.remove(sale)
    for i, sale in enumerate(sales):
        psa_old = Product_Stock_Attributes.query.filter_by(stock_id=1, product_id=sale.pricinglog.product_id).first()
        psa_new, _ = db.session.query(
            Product_Stock_Attributes, Product
        ).filter(
            Product_Stock_Attributes.product_id==Product.id
        ).filter(
            Product.internal_id==list(product_ids.keys())[i]
        ).filter(
            Product_Stock_Attributes.stock_id==1
        ).first()
        db.session.add(StockUpdateQueue(int(product_ids[list(product_ids.keys())[i]]), psa_old.id, psa_old.quantity))
        db.session.add(StockUpdateQueue(-1 * int(product_ids[list(product_ids.keys())[i]]), psa_new.id, psa_new.quantity))
        db.session.commit()
