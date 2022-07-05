# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingAction, Marketplace
from sqlalchemy import case, or_
from datetime import datetime


subquery_m30 = db.session.query(
    PricingAction.product_id.label('p_id'), PricingAction.name.label('pa_name')
).filter(
    PricingAction.name == 'Abverkauf -30%'
).subquery()

subquery_m20 = db.session.query(
    PricingAction.product_id.label('p_id'), PricingAction.name.label('pa_name')
).filter(
    PricingAction.name == 'Abverkauf -20%'
).subquery()

subquery_30 = db.session.query(
    PricingAction.product_id.label('p_id'), PricingAction.name.label('pa_name')
).filter(
    PricingAction.name == 'Abverkauf 30%'
).subquery()

subquery_20 = db.session.query(
    PricingAction.product_id.label('p_id'), PricingAction.name.label('pa_name')
).filter(
    PricingAction.name == 'Abverkauf 20%'
).subquery()

query = db.session.query(
    Product
).outerjoin(
    subquery_m30, subquery_m30.c.p_id == Product.id
).outerjoin(
    subquery_m20, subquery_m20.c.p_id == Product.id
).outerjoin(
    subquery_30, subquery_30.c.p_id == Product.id
).outerjoin(
    subquery_20, subquery_20.c.p_id == Product.id
).add_columns(
    case([(subquery_m30.c.pa_name=='Abverkauf -30%', 1)], else_=0).label('abvk_m30'),
    case([(subquery_m20.c.pa_name=='Abverkauf -20%', 1)], else_=0).label('abvk_m20'),
    case([(subquery_30.c.pa_name=='Abverkauf 30%', 1)], else_=0).label('abvk_30'),
    case([(subquery_20.c.pa_name=='Abverkauf 20%', 1)], else_=0).label('abvk_20')
).filter(
    or_(
        case([(subquery_m30.c.pa_name=='Abverkauf -30%', 1)], else_=0) == 0,
        case([(subquery_m20.c.pa_name=='Abverkauf -20%', 1)], else_=0) == 0,
        case([(subquery_30.c.pa_name=='Abverkauf 30%', 1)], else_=0) == 0,
        case([(subquery_20.c.pa_name=='Abverkauf 20%', 1)], else_=0) == 0
    )
).all()

le = len(query)
marketplaces = Marketplace.query.all()
start = datetime.strptime('01.01.2020', '%d.%m.%Y')
end = datetime.strptime('01.01.2100', '%d.%m.%Y')

for i, (p, abvk_m30, abvk_m20, abvk_30, abvk_20) in enumerate(query):
    print(f'{i}/{le}')
    for pr in [-30, -20, 20, 30]:
        new_pricingaction = PricingAction(f'Abverkauf {pr}%', start, end, 'Automatisch generiert', p.id, [1])
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 3, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=pr == 0,
                                         mp_ids=[mp.id for mp in marketplaces])