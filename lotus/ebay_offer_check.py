# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, Marketplace_Product_Attributes, Marketplace, MPReport, Stock, Product_Stock_Attributes
import ebay_api
from datetime import datetime


err_ids = {}
p_ids = []

ebay = Marketplace.query.filter_by(name='Ebay').first()

query = db.session.query(
    Product, Marketplace_Product_Attributes
).filter(
    Product.id == Marketplace_Product_Attributes.product_id
).filter(
    Marketplace_Product_Attributes.marketplace_id == ebay.id
).filter(
    Marketplace_Product_Attributes.uploaded == True
).filter(
    Product.id.in_(p_ids) if p_ids else True
).order_by(
    Product.id.desc()
).all()
print(len(query))
not_found = 0
active = 0
active_short_sell = 0
active_pre_order = 0
pos_short_sell_quant = 0
pos_pre_order_quant = 0
oos_quant = 0   # OUT_OF_STOCK
strikes = 0
m=0
for p, mpa in query:
    if strikes == 10:
        break
    differing_quant = False
    differing_price = False
    print('---------------------')
    print(p.id)
    err_1 = False
    err_2 = False
    try:
        r = ebay_api.get_offer(p.internal_id)
        data = r.json()
    except Exception as e:
        print(e)
        err_1 = True
    if err_1 is True:
        try:
            r = ebay_api.get_offer(p.internal_id)
            data = r.json()
        except Exception as e:
            print(e)
            err_2 = True
    if err_2 is True:
        try:
            r = ebay_api.get_offer(p.internal_id)
            data = r.json()
        except Exception as e:
            print(e)
            strikes += 1
            continue
    try:
        if "errors" in data:
            not_found += 1
            not_listed = True
            quant = None
            price = None
            p.mp_offer_check(ebay.id, quant, price, not_listed)
        else:
            not_listed = False
            offer = data["offers"][0]
            if offer["listing"]["listingStatus"] == 'OUT_OF_STOCK':
                quant = 0
                oos_quant += 1
            else:
                if "availableQuantity" not in offer:
                    r = mpa.product.mp_prq_update(marketplace_id=mpa.marketplace_id, quantity=True, price=True)
                    print(r.text)
                    r = ebay_api.get_offer(p.internal_id)
                    data = r.json()
                    offer = data["offers"][0]
                quant = offer["availableQuantity"]
                active += int(offer["availableQuantity"]>0)
                active_short_sell += int(offer["availableQuantity"]>0) * int(p.short_sell is True)
                active_pre_order += int(offer["availableQuantity"]>0) * int(p.release_date > datetime.now()) if p.release_date else 0
            price = float(offer["pricingSummary"]["price"]["value"])
            p.mp_offer_check(ebay.id, quant, price, not_listed)

    except Exception as e:
        print(e)
        err_ids[p.id] = data
print(err_ids)
if strikes < 10:
    est_uploaded = len(query)

    stock_ids = db.session.query(Stock.id).filter_by(owned=True).all()

    psas = db.session.query(
        Product_Stock_Attributes.product_id
    ).filter(
        Product_Stock_Attributes.quantity > 0
    ).filter(
        Product_Stock_Attributes.stock_id.in_(stock_ids)
    ).subquery()

    est_active = db.session.query(
        Marketplace_Product_Attributes
    ).join(
        psas, psas.c.product_id==Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == ebay.id
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).count()

    est_active_short_sell = db.session.query(
        Marketplace_Product_Attributes, Product
    ).join(
        psas, psas.c.product_id==Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == ebay.id
    ).filter(
        Marketplace_Product_Attributes.product_id == Product.id
    ).filter(
        Product.short_sell == True
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).count()

    est_active_pre_order = db.session.query(
        Marketplace_Product_Attributes, Product
    ).join(
        psas, psas.c.product_id==Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == ebay.id
    ).filter(
        Marketplace_Product_Attributes.product_id == Product.id
    ).filter(
        Product.release_date > datetime.now()
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).count()

    print(est_uploaded)
    print(est_active)
    print(est_active_short_sell)
    print(est_active_pre_order)
    print(est_uploaded-est_active)
    print(est_uploaded-not_found)
    print(active)
    print(active_short_sell)
    print(active_pre_order)
    print(oos_quant)
    print(ebay.id)
    db.session.add(MPReport(est_uploaded=est_uploaded, est_active=est_active, est_active_short_sell=est_active_short_sell, est_active_pre_order=est_active_pre_order, est_inactive=est_uploaded-est_active, uploaded=est_uploaded-not_found,
                            active=active, active_short_sell=active_short_sell, active_pre_order=active_pre_order, inactive=oos_quant, marketplace_id=ebay.id))
    db.session.commit()

