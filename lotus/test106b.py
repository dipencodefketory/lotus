# -*- coding: utf-8 -*-

from lotus import db, Product


p = Product.query.filter_by(id=35051).first()
p.add_basic_product_data(1)
