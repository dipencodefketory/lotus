# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingBundle, PricingRule, PricingAction, Sale, PricingLog, Marketplace_Product_Attributes, Product_Stock_Attributes
import idealo_offer

from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta


subquery = db.session.query(
    PricingLog.product_id.label('product_id'), func.sum(Sale.quantity).label('num'), func.sum(Sale.selling_price).label('rev')
).filter(
    and_(
        PricingLog.id == Sale.pricinglog_id,
        Sale.quantity > 0,
        Sale.timestamp >= datetime.now() - timedelta(hours=24),
        PricingAction.product_id == PricingLog.product_id,
        PricingAction.active == True
    )
).group_by(
    PricingLog.product_id
).subquery()

action_sq = db.session.query(
    PricingAction.product_id.label('p_id'), PricingAction.name.label('action_name')
).filter(
    PricingAction.active == True
).subquery()

query = db.session.query(
    Product, PricingBundle, PricingRule, PricingAction
).join(
    action_sq, action_sq.c.p_id == Product.id
).join(
    Product_Stock_Attributes, Product_Stock_Attributes.product_id == Product.id
).outerjoin(
    subquery, subquery.c.product_id == Product.id
).add_columns(
    func.coalesce(subquery.c.num, 0), func.coalesce(subquery.c.rev, 0), action_sq.c.action_name
).filter(
    and_(
        Product.pricing_bundle_id == PricingBundle.id,
        PricingRule.pricing_bundle_id == PricingBundle.id,
        PricingAction.product_id == Product.id,
        PricingRule.then_strategy == PricingAction.name,
        PricingRule.if_strategy == action_sq.c.action_name,
        PricingRule.if_sale_fail_h != None,
        or_(
            and_(PricingRule.if_sale_rev != None, PricingRule.if_sale_rev > func.coalesce(subquery.c.rev, 0)),
            and_(PricingRule.if_sale_num != None, PricingRule.if_sale_num > func.coalesce(subquery.c.num, 0))
        ),
        Product_Stock_Attributes.stock_id == 1,
        Product_Stock_Attributes.quantity > 0,
    )
).order_by(
    Product.id
).all()

for p, _, _, pa, _, _, _ in query:
    for pr_a in p.actions:
        for strategy in pr_a.strategies:
            strategy.active = False
            pr_a.active = False
        db.session.commit()
    for strategy in pa.strategies:
        strategy.active = True
        authorization = idealo_offer.get_access_token()
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=p.id, marketplace_id=strategy.marketplace_id).first()
        if mpa.uploaded and mpa.upload_clearance:
            try:
                p.generate_mp_price(marketplace_id=strategy.marketplace_id, strategy_label=strategy.label, min_margin=strategy.prc_margin / 100 if strategy.prc_margin is not None else None,
                                    max_margin=strategy.prc_max_margin / 100 if strategy.prc_max_margin is not None else None, rank=strategy.rank if strategy.rank else 0,
                                    ext_offers=p.get_mp_ext_offers(strategy.marketplace_id), authorization=authorization)
            except Exception as e:
                print(e)
    pa.active = True
    db.session.commit()
