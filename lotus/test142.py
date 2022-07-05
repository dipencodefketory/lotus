# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Marketplace, PricingAction, PricingStrategy
from datetime import datetime

start = datetime.strptime('2021-01-01', '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
end = datetime.strptime('2100-01-01', '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
stock_id = 1
mps = Marketplace.query.all()
mp_ids = [mp.id for mp in mps]
pas = PricingAction.query.filter(PricingAction.name.in_(['Marktpreis 0-15%', 'Marktpreis 0-20%'])).all()
p_ids = [pa.product_id for pa in pas]
ps = Product.query.filter(Product.id.notin_(p_ids)).order_by(Product.id).all()
le = len(ps)
print(le)
for j, p in enumerate(ps):
    print(f'{j+1}/{le}')
    new_pricingaction = PricingAction(f'Marktpreis 0-15%', start, end, 'Automatisch generiert', p.id, [stock_id])
    new_pricingaction.active = False
    db.session.add(new_pricingaction)
    db.session.commit()
    new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 0, 'prc_max_margin': 15, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                     active=False, mp_ids=mp_ids)
    new_pricingaction = PricingAction(f'Marktpreis 0-20%', start, end, 'Automatisch generiert', p.id, [stock_id])
    new_pricingaction.active = False
    db.session.add(new_pricingaction)
    db.session.commit()
    new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 0, 'prc_max_margin': 20, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                     active=False, mp_ids=mp_ids)
