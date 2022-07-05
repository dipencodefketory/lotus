# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, PricingAction, PricingStrategy, PricingLog, Sale, Marketplace, PrActionReport
from sqlalchemy import func
from datetime import datetime, timedelta

proc_prods = []
mps = Marketplace.query.all()
pa_names = db.session.query(PricingAction.name).filter(PricingAction.archived == False).group_by(PricingAction.name).all()
pa_names = [pa_name[0] for pa_name in pa_names]
for mp in mps:
    d = datetime.now() - timedelta(days=1)
    ###########################
    query = db.session.query(
        PricingLog.product_id, Sale
    ).filter(
        PricingLog.marketplace_id == mp.id
    ).filter(
        Sale.pricinglog_id == PricingLog.id
    ).filter(
        Sale.timestamp >= d.replace(hour=0, minute=0, second=0, microsecond=0)
    ).filter(
        Sale.timestamp <= d.replace(hour=23, minute=59, second=59, microsecond=999999)
    ).all()

    p_ids = [p_id for p_id, _ in query]

    query = db.session.query(
        Product, PricingLog
    ).filter(
        PricingLog.product_id == Product.id
    ).filter(
        PricingLog.marketplace_id == mp.id
    ).filter(
        Product.id.in_(p_ids) if p_ids else False
    ).filter(
        Product.id.notin_(proc_prods)
    ).order_by(
        Product.id, PricingLog.set_date
    ).all()
    le = len(query)
    if query:
        curr_p_id = query[0][0].id
        curr_ps_id = query[0][1].pricingstrategy_id
        curr_price = query[0][1].selling_price
        for i, (p, log) in enumerate(query):
            print(f'{i}/{le}')
            if p.id == curr_p_id:
                if curr_price == log.selling_price:
                    if curr_ps_id is not None:
                        if log.pricingstrategy_id is None:
                            log.pricingstrategy_id = curr_ps_id
                            print('--------------------------')
                            print(p.id)
                            print(curr_ps_id)
                            print(curr_price)
                            print('--------------------------')
                            db.session.commit()
                        else:
                            curr_ps_id = log.pricingstrategy_id
                    else:
                        curr_ps_id = log.pricingstrategy_id
                else:
                    curr_price = log.selling_price
                    curr_ps_id = log.pricingstrategy_id
            else:
                curr_p_id = p.id
                curr_price = log.selling_price
                curr_ps_id = log.pricingstrategy_id
    proc_prods += p_ids
    ###########################
    all_names = [pa_name for pa_name in pa_names]
    print(d)
    print(mp.name)
    pas = db.session.query(PricingAction.name).filter(PricingAction.archived == False).group_by(PricingAction.name).order_by(PricingAction.name).all()

    query = db.session.query(
        PricingAction.name, func.count(PricingStrategy.id), func.count(PricingLog.id), func.sum(Sale.quantity)
    ).filter(
        PricingAction.id == PricingStrategy.pricingaction_id
    ).filter(
        PricingLog.pricingstrategy_id == PricingStrategy.id
    ).filter(
        PricingLog.marketplace_id == mp.id
    ).filter(
        Sale.pricinglog_id == PricingLog.id
    ).filter(
        Sale.timestamp >= d.replace(hour=0, minute=0, second=0, microsecond=0)
    ).filter(
        Sale.timestamp <= d.replace(hour=23, minute=59, second=59, microsecond=999999)
    ).group_by(
        PricingAction.name
    ).all()

    for name, _, _, num in query:
        if name in all_names:
            all_names.remove(name)
        db.session.add(PrActionReport(name, 0, num, mp.id, init_date=d))
        db.session.commit()
    print(all_names)
    for name in all_names:
        db.session.add(PrActionReport(name, 0, 0, mp.id, init_date=d))
        db.session.commit()

    print(query)

    query = db.session.query(
        func.count(PricingLog.id), func.sum(Sale.quantity)
    ).filter(
        PricingLog.pricingstrategy_id == None
    ).filter(
        Sale.pricinglog_id == PricingLog.id
    ).filter(
        PricingLog.marketplace_id == mp.id
    ).filter(
        Sale.timestamp >= d.replace(hour=0, minute=0, second=0, microsecond=0)
    ).filter(
        Sale.timestamp <= d.replace(hour=23, minute=59, second=59, microsecond=999999)
    ).group_by(

    ).first()
    if query:
        db.session.add(PrActionReport('Keine Aktion', 0, query[1] if query[1] else 0, mp.id, init_date=d))
        db.session.commit()
    else:
        db.session.add(PrActionReport('Keine Aktion', 0, 0, mp.id, init_date=d))
        db.session.commit()

    print(query)
    print('----------------------------')