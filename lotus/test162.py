# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingAction, ProductCategory
from datetime import datetime, timedelta


toy_cat = ProductCategory.query.filter_by(name='Spielzeug').first()
toy_cat_ids = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]

query_1 = db.session.query(
    Product, PricingAction
).filter(
    Product.id == PricingAction.product_id
).filter(
    PricingAction.active == True
).filter(
    PricingAction.name.like('%Abverkauf 0%')
).filter(
    Product.category_id.in_(toy_cat_ids)
).all()

p_ids = [p.id for p, _ in query_1]

query = db.session.query(
    Product, PricingAction
).filter(
    Product.id == PricingAction.product_id
).filter(
    PricingAction.active == False
).filter(
    PricingAction.name.like('%Abverkauf 10%')
).filter(
    Product.id.in_(p_ids)
).filter(
    Product.category_id.in_(toy_cat_ids)
).all()

le = len(query)
for i, (product, pricing_action) in enumerate(query):
    print(f'{i+1}/{le}')
    for pa in product.actions:
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
    for mpa in product.marketplace_attributes:
        mpa.pr_update_dur = 6
        k = datetime.now().hour // 6
        mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
    db.session.commit()
