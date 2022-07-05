# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingAction, Marketplace

from sqlalchemy import func, or_
from datetime import datetime
import re
import csv


marketplaces = Marketplace.query.all()
ps = Product.query.all()

start = datetime.strptime('01.01.2020', '%d.%m.%Y')
end = datetime.strptime('01.01.2100', '%d.%m.%Y')

for p in ps:
    for pr in [-30, -20, 20, 30]:
        new_pricingaction = PricingAction(f'Abverkauf {pr}%', start, end, 'Automatisch generiert', p.id, [1])
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 3, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=pr == 0,
                                         mp_ids=[mp.id for mp in marketplaces])
