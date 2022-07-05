# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Marketplace_Product_Attributes, Marketplace_ProductCategory
from sqlalchemy import or_


mpas = Marketplace_Product_Attributes.query.filter_by(marketplace_id=2).order_by(Marketplace_Product_Attributes.product_id).all()
le = len(mpas)
for i, mpa in enumerate(mpas):
    print(f'{i}/{le}\t{mpa.product_id}')
    l_mpa = Marketplace_Product_Attributes(3, mpa.product_id)
    l_mpa.commission = 0.01
    l_mpa.name = mpa.name if mpa.name else mpa.product.name
    l_mpa.mp_hsp_id = mpa.product.hsp_id
    l_mpa.selling_price = mpa.selling_price
    l_mpa.block_selling_price = False
    db.session.add(l_mpa)
    db.session.commit()
