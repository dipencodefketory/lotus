# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*

from lotus import db
from basismodels import Stock, Product_Stock_Attributes, Product, PricingAction
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

stock_ids = db.session.query(Stock.id).filter_by(owned=True).all()

not_ids = [294, 3200, 12703, 14108, 16121, 12933, 5033, 8089, 154, 11441, 8856, 10304, 9182]
psas = db.session.query(
    Product_Stock_Attributes.product_id, Product
).filter(
    or_(
        and_(Product_Stock_Attributes.quantity == 102, Product.short_sell == True),
        and_(Product_Stock_Attributes.quantity == 2, Product.short_sell == False)
    )
).filter(
    Product.id == Product_Stock_Attributes.product_id
).filter(
    Product.id.notin_(not_ids)
).filter(
    Product_Stock_Attributes.stock_id.in_(stock_ids)
).all()

p_ids = [p_id for p_id, _ in psas]

query = db.session.query(
    Stock, Product_Stock_Attributes, Product, PricingAction
).filter(
    Product.id.in_(p_ids)
).filter(
    Stock.id == Product_Stock_Attributes.stock_id
).filter(
    Product_Stock_Attributes.product_id == Product.id
).filter(
    Product_Stock_Attributes.avail_date <= datetime.now()
).filter(
    Product_Stock_Attributes.termination_date >= datetime.now()
).filter(
    Product.buying_price >= Product_Stock_Attributes.buying_price
).filter(
    Product.id == PricingAction.product_id
).filter(
    Stock.owned == False
).filter(
    PricingAction.active == False
).filter(
    PricingAction.name.like('%Abverkauf 0%')
).filter(
    Product_Stock_Attributes.quantity > 5
).all()
no_action_ids = []

le = len(query)
for i, (s, psa, p, pricing_action) in enumerate(query):
    print('-----------------------------')
    print(f'{i}/{le}')
    print(f'Product-ID: {p.id}')
    for pa in pricing_action.product.actions:
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
    for mpa in p.marketplace_attributes:
        mpa.pr_update_dur = 6
        k = datetime.now().hour // 6
        mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
    db.session.commit()
print(len(query))