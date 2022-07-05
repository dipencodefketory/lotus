# -*- coding: utf-8 -*

from lotus import db
from basismodels import Product, PricingAction, Marketplace
import idealo_offer

from sqlalchemy import func
from datetime import datetime


'''
stock_id = 1
marketplaces = Marketplace.query.all()
for i, p in enumerate(ps):
    print(f'{i}/{le}')
    for action in p.actions:
        for s in action.strategies:
            db.session.delete(s)
            db.session.commit()
        db.session.delete(action)
        db.session.commit()
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.strptime('2100-01-01', '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)

    new_pricingaction = PricingAction('Kuchenboden', start, end, 'Automatisch generiert', p.id, [stock_id])
    db.session.add(new_pricingaction)
    db.session.commit()
    new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 30, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                     mp_ids=[mp.id for mp in marketplaces])

    new_pricingaction = PricingAction('Fix Preis', start, end, 'Automatisch generiert', p.id, [stock_id])
    db.session.add(new_pricingaction)
    db.session.commit()
    new_pricingaction.add_strategies({'all': {'label': 0, 'rank': None, 'prc_margin': None, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                     mp_ids=[mp.id for mp in marketplaces])

    for pr in [0, 5, 10, 15, 20, 25, 40]:
        new_pricingaction = PricingAction(f'Marktpreis {pr}%', start, end, 'Automatisch generiert', p.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=False,
                                         mp_ids=[mp.id for mp in marketplaces])
    for pr in [-10, 0, 5, 10]:
        new_pricingaction = PricingAction(f'Abverkauf {pr}%', start, end, 'Automatisch generiert', p.id, [stock_id])
        new_pricingaction.active = True if pr == 0 else False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 3, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=pr == 0,
                                         mp_ids=[mp.id for mp in marketplaces])
    for pr, max_pr in [(0, 10), (0, 15), (0, 20)]:
        new_pricingaction = PricingAction(f'Marktpreis {pr}-{max_pr}%', start, end, 'Automatisch generiert', p.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': pr, 'prc_max_margin': max_pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         active=False, mp_ids=[mp.id for mp in marketplaces])
'''
query = db.session.query(
    PricingAction.product_id
).filter(
    PricingAction.name == 'Marktpreis 15%'
).group_by(
    PricingAction.product_id
).all()

p_ids = [el[0] for el in query]

ps = Product.query.all()
le = len(ps)
print(le)

stock_id = 1
mps = Marketplace.query.all()
start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end = datetime.strptime('2100-01-01', '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
for i, p in enumerate(ps):
    if p.id not in p_ids:
        print(f'{i}/{le}')
        new_pricingaction = PricingAction(f'Marktpreis 15%', start, end, 'Automatisch generiert', p.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 15, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         active=False, mp_ids=[mp.id for mp in mps])
'''
query = db.session.query(
    PricingAction.product_id
).group_by(
    PricingAction.product_id
).having(
    func.count(PricingAction.id) < 16
).all()

print(query)
print(len(query))
'''