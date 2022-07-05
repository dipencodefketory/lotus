# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingAction, PricingLog, Sale, Product_Stock_Attributes

from sqlalchemy import func
from datetime import datetime, timedelta


query = db.session.query(
    func.count(Sale.id), PricingLog.product_id
).filter(
    Sale.pricinglog_id == PricingLog.id
).group_by(
    PricingLog.product_id
).all()

p_ids = [el[1] for el in query]

print(len(p_ids))

query = db.session.query(
    Product, PricingAction, Product_Stock_Attributes
).filter(
    PricingAction.product_id == Product.id
).filter(
    Product_Stock_Attributes.product_id == Product.id
).filter(
    Product_Stock_Attributes.stock_id == 1
).filter(
    PricingAction.name == 'Abverkauf 5%'
).filter(
    Product.id.notin_(p_ids)
).filter(
    Product.id >= 4960
).filter(
    Product_Stock_Attributes.quantity == 0
).order_by(
    Product_Stock_Attributes.quantity.desc()
).all()

le = len(query)

for i, (p, pricing_action, psa) in enumerate(query):
    print(f'{i}/{le}\t{p.id}\tQUANT: {psa.quantity}')
    for pa in p.actions:
        pa.active = False
        for strategy in pa.strategies:
            strategy.active = False
    db.session.commit()
    pricing_action.active = True
    if pricing_action.promotion_quantity != None:
        pricing_action.sale_count = 0
    for strategy in pricing_action.strategies:
        strategy.active = True
        if strategy.promotion_quantity != None:
            strategy.sale_count = 0
    db.session.commit()
