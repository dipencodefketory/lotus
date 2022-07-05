# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Marketplace_Product_Attributes, Marketplace_ProductCategory
from sqlalchemy import or_


query = db.session.query(
    Product, Marketplace_Product_Attributes, Marketplace_ProductCategory
).filter(
    Product.category_id == Marketplace_ProductCategory.productcategory_id
).filter(
    Marketplace_ProductCategory.marketplace_system_id != None
).filter(
    Marketplace_ProductCategory.productcategory_id != None
).filter(
    Product.id == Marketplace_Product_Attributes.product_id
).filter(
    Marketplace_Product_Attributes.marketplace_id == 2
).filter(
    Marketplace_ProductCategory.marketplace_id == 2
).filter(
    or_(Marketplace_Product_Attributes.mp_cat_id == None, Marketplace_Product_Attributes.mp_cat_id == '')
).order_by(
    Product.id
).all()
le=len(query)
for i, (p, mpa, mpc) in enumerate(query):
    print(f'{i}/{le}')
    mpa.mp_cat_id = mpc.marketplace_system_id
    db.session.commit()