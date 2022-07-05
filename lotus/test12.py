#-*- coding: utf-8 -*-

from lotus import db, Product, Marketplace_Product_Attributes, Product_Stock_Attributes
from datetime import datetime, timedelta
import idealo_offer


idealo_auth = idealo_offer.get_access_token()
query = db.session.query(
    Product, Marketplace_Product_Attributes, Product_Stock_Attributes
).filter(
    Marketplace_Product_Attributes.product_id == Product.id
).filter(
    Product_Stock_Attributes.product_id == Product.id
).filter(
    Product_Stock_Attributes.stock_id == 1
).filter(
    Product_Stock_Attributes.quantity > 0
).filter(
    Marketplace_Product_Attributes.marketplace_id == 1
).filter(
    Marketplace_Product_Attributes.uploaded == True
).all()

le = len(query)
start = datetime.now()
for i, (p, mpa, _) in enumerate(query):
    if datetime.now() - timedelta(minutes=50) > start:
        start = datetime.now()
        idealo_auth = idealo_offer.get_access_token()
    print('-----------------------')
    print(f'{i}/{le}')
    print(p.id)
    try:
        r = p.mp_update(1, shipping_time=True, quantity=True, authorization=idealo_auth)
        print(r)
    except Exception as e:
        print(e)