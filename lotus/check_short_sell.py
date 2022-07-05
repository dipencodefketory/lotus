# -*- coding: utf-8 -*

from lotus import db
from basismodels import Product, Stock, Order, Product_Stock_Attributes, PSAUpdateQueue

import csv
from sqlalchemy import func, or_
from datetime import datetime, timedelta

p_ids = []
ps = Product.query.filter(Product.id.in_(p_ids) if p_ids else True).filter_by(short_sell=False).all()
le = len(ps)
count = 0
for i, p in enumerate(ps):
    print(f'{i}/{le}')
    stock, buying_price = p.get_cheapest_buying_price_all()
    if stock is None:
        stock = Stock.query.filter_by(id=1).first()
    p.cheapest_stock_id = stock.id if stock else None
    update = False
    if p.cheapest_buying_price != buying_price:
        update = True
    p.cheapest_buying_price = buying_price
    if p.cheapest_stock_id not in [None, 1] or update is True:
        p_ids.append(p.id)
        db.session.add(PSAUpdateQueue(p.id))
        db.session.commit()
        count += 1
print(count)
print(p_ids)