# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Stock, Product_Stock_Attributes, Product, Marketplace
import afterbuy_api
import idealo_offer

from datetime import datetime
import xml.etree.ElementTree as ETree


stock_ids = db.session.query(Stock.id).filter_by(owned=True).all()

psas = db.session.query(
    Product_Stock_Attributes.product_id
).filter(
    Product_Stock_Attributes.quantity > 0
).filter(
    Product_Stock_Attributes.stock_id.in_(stock_ids)
).subquery()

products = Product.query.join(
    psas, psas.c.product_id==Product.id
).order_by(Product.internal_id.desc()).all()

own_stock = Stock.query.filter_by(owned=True).order_by(Stock.id).first()
marketplace = Marketplace.query.filter_by(name='Idealo').first()

request_quant = 250
i = 0
while i*request_quant <= len(products):
    print(i)
    r = afterbuy_api.get_shop_products({'ProductID': [product.internal_id for product in products[i*request_quant:(i+1)*request_quant]]})
    tree = ETree.fromstring(r.text)
    p_tree = [item for item in tree.iter() if item.tag == 'Product']
    for p in p_tree:
        afterbuy_id = p.find('ProductID').text
        auction_quant = p.find('AuctionQuantity').text
        product = Product.query.filter_by(internal_id=afterbuy_id).first()
        if product:
            print(product.id)
            print(auction_quant)
            try:
                if product.get_own_stock_attributes() is None:
                    psa = Product_Stock_Attributes('Neu & OVP', int(auction_quant), None, 0, 0.19, 0, datetime.now(), datetime.strptime('01.01.3000', '%d.%m.%Y'), product.id, own_stock.id)
                    db.session.add(psa)
                else:
                    product.get_own_stock_attributes().quantity = int(auction_quant)
                db.session.commit()
            except Exception as e:
                print(product.id)
                print(str(e))
    i += 1
