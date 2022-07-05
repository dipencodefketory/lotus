# -*- coding: utf-8 -*-

from lotus import *

pricing_actions = PricingAction.query.filter(
    PricingAction.end < datetime.now()
).filter(
    PricingAction.active == True
).all()

for pricing_action in pricing_actions:
    pricing_action.active = False
    for strategy in pricing_action.strategies:
        strategy.active = False
    db.session.commit()

activatable_p_ids = []

products = Product.query.all()

for product in products:
    pa_query = PricingAction.query.filter(
        PricingAction.product_id == product.id
    ).filter(
        PricingAction.active == False
    ).all()

    # noinspection PyComparisonWithNone
    query = db.session.query(
        PricingAction
    ).filter(
        PricingAction.product_id==product.id
    ).filter(
        PricingAction.promotion_quantity != None
    ).filter(
        PricingAction.sale_count != None
    ).all()

    ids = [item.id for item in query if item.sale_count >= item.promotion_quantity]

    if len(product.actions) == len(pa_query):
        pa = db.session.query(
            PricingAction
        ).filter(
            PricingAction.start <= datetime.now()
        ).filter(
            PricingAction.end >= datetime.now()
        ).filter(
            PricingAction.product_id == product.id
        ).filter(
            PricingAction.archived == False
        ).filter(
            PricingAction.id.notin_(ids)
        ).order_by(
            PricingAction.id.desc()
        ).first()

        if pa:
            pa.active = True
            for strategy in pa.strategies:
                strategy.active = True
            db.session.commit()
    else:
        pa = PricingAction.query.filter(
            PricingAction.start == datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).filter(
            PricingAction.product_id == product.id
        ).filter(
            PricingAction.archived == False
        ).filter(
            PricingAction.id.notin_(ids)
        ).all()

        if pa:
            activatable_p_ids.append(product.id)


subquery = db.session.query(
    PricingAction.parent_id
).filter(
    PricingAction.parent_id != None
)

soon_to_end = db.session.query(
    PricingAction.product_id
).filter(
    PricingAction.end < datetime.now() + timedelta(days=5)
).filter(
    PricingAction.active == True
).filter(
    PricingAction.id.notin_(subquery)
).group_by(
    PricingAction.product_id
).all()

product_ids = [result.product_id for result in soon_to_end]

multiple_active_query = db.session.query(
    Product, func.count(PricingAction.id)
).filter(
    PricingAction.product_id == Product.id
).filter(
    PricingAction.active == True
).group_by(
    Product.id
).having(
    func.count(PricingAction.id)>1
).all()

multiple_active = [result[0].id for result in multiple_active_query]

msg = ''
if product_ids or activatable_p_ids:
    if product_ids:
        msg += 'In den kommenden 5 Tagen laufen zu den folgenden Produkten aktive Pricing-Aktionen ohne Nachfolger aus:\r\n'
        for product_id in product_ids:
            msg += str(product_id)+'\r\n'
    if (product_ids and activatable_p_ids) or (product_ids and multiple_active):
        msg += '-----------------------\r\n'
    if activatable_p_ids:
        msg += 'Zu den folgenden Produkten kann ab heute eine Aktion aktiviert werden:\r\n'
        for product_id in activatable_p_ids:
            msg += str(product_id)+'\r\n'
    if activatable_p_ids and multiple_active:
        msg += '-----------------------\r\n'
    if multiple_active:
        msg += 'Zu den folgenden Produkten sind mehr als eine Aktion aktiv:\r\n'
        for product_id in multiple_active:
            msg += str(product_id)+'\r\n'
    send_email('Infos zu Pricing-Aktionen', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)



