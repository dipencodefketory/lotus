# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Marketplace_Product_Attributes, ProductCategory
import idealo_offer

from datetime import datetime, timedelta


kids_cat = ProductCategory.query.filter_by(name='Kinder').first()
hc_cat = ProductCategory.query.filter_by(name='Haushalt & Küche').first()

query = db.session.query(
    Product, Marketplace_Product_Attributes
).filter(
    Product.id == Marketplace_Product_Attributes.product_id
).filter(
    Marketplace_Product_Attributes.marketplace_id == 1
).filter(
    Marketplace_Product_Attributes.uploaded == True
).filter(
    Product.id > 20777
).filter(
    Marketplace_Product_Attributes.upload_clearance == True
).order_by(
    Product.id
).all()

authorization = idealo_offer.get_access_token()
dt = datetime.now()
le = len(query)
err_ids = []
for i, (p, mpa) in enumerate(query):
    try:
        print(f'{i}/{le}\t{p.id}')
        if datetime.now() - timedelta(minutes=50) > dt:
            dt = datetime.now()
            authorization = idealo_offer.get_access_token()
        r = p.mp_update(authorization=authorization, marketplace_id=1, mpn=True)
        if not r.ok:
            err_ids.append(p.id)
            print('--------------------------\nERR\n--------------------------')
    except Exception as e:
        print(e)
        break
print(err_ids)