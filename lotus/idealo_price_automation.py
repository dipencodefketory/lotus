# -*- coding: utf-8 -*-

from lotus import db, send_email
from basismodels import Stock, Marketplace_Product_Attributes, Product_Stock_Attributes, Marketplace, Product, PricingAction, PricingStrategy
import idealo_offer
from datetime import datetime, timedelta

dt = datetime.now()
authorization = idealo_offer.get_access_token()
stock_ids = db.session.query(Stock.id).filter(Stock.owned==True).all()

psas = db.session.query(
    Product_Stock_Attributes.product_id
).filter(
    Product_Stock_Attributes.quantity > 0
).filter(
    Product_Stock_Attributes.stock_id.in_(stock_ids)
).subquery()
print("psasquery====",psas)
marketplace = Marketplace.query.filter_by(name='Idealo').first()

update_time = datetime.now().replace(minute=0, second=0, microsecond=0)

query = db.session.query(Product, Marketplace_Product_Attributes, PricingAction, PricingStrategy).join(
    psas, psas.c.product_id==Product.id
).filter(
    PricingAction.product_id==Product.id
).filter(
    PricingStrategy.pricingaction_id==PricingAction.id
).filter(
    PricingStrategy.marketplace_id==marketplace.id
).filter(
    PricingStrategy.active==True
).filter(
    PricingAction.active==True
).filter(
    Marketplace_Product_Attributes.product_id==Product.id
).filter(
    Marketplace_Product_Attributes.marketplace_id==marketplace.id
).filter(
    Marketplace_Product_Attributes.pr_update_ts==update_time
).order_by(
    Product.id
).all()
print("query====",query)
sent_own = []
sent_kb = []
no_result = []
neg_margin = []
ult_err = []
no_stock = []
not_listed = []
error_dict = {}
for p, mpa, pa, ps  in query:
    if datetime.now() - timedelta(minutes=50) > dt:
        dt = datetime.now()
        authorization = idealo_offer.get_access_token()
    try:
        if mpa.uploaded:
            if ps.label in [0]:
                response = p.generate_mp_price(marketplace.id, strategy_label=ps.label, strategy_id=ps.id, authorization=authorization)
            if ps.label in [1, 2]:
                response = p.generate_mp_price(marketplace.id, strategy_label=ps.label, strategy_id=ps.id, min_margin=ps.prc_margin/100 if ps.prc_margin is not None else None,
                                               max_margin=ps.prc_max_margin/100 if ps.prc_max_margin is not None else None, rank=ps.rank if ps.rank is not None else 0,
                                               ext_offers=p.get_mp_ext_offers(marketplace.id), authorization=authorization)
            elif ps.label == 3:
                response = p.generate_mp_price(marketplace.id, strategy_label=ps.label, strategy_id=ps.id, min_margin=ps.prc_margin/100 if ps.prc_margin is not None else None, rank=ps.rank if ps.rank is not None else 0,
                                               authorization=authorization)
            '''
            if response[7] is True:
                mpa.pr_update_dur = 6
            else:
                if p.release_date is not None:
                    if p.release_date <= datetime.now():
                        mpa.pr_update_dur *= 2
                else:
                    mpa.pr_update_dur *= 2
            '''
            mpa.pr_update_ts = update_time + timedelta(hours=mpa.pr_update_dur)
            db.session.commit()
            sent_own.append(str(p.id)) if response[0] else None
            sent_kb.append(str(p.id)) if response[1] else None
            no_result.append(str(p.id)) if response[2] else None
            neg_margin.append(str(p.id)) if response[3] else None
            ult_err.append(str(p.id)) if response[4] else None
            no_stock.append(str(p.id)) if response[5] else None
            not_listed.append(str(p.id)) if response[6] else None
            print(f'{p.id} - OK')
        else:
            print(f'{p.id} - NOT UPLOADED')
            mpa.pr_update_ts = update_time + timedelta(hours=mpa.pr_update_dur)
            db.session.commit()
    except Exception as e:
        error_dict[p.id] = str(e)
        print(f'{p.id} - {e}')
        print('----------------')
        print('UPDATE TIME')
        try:
            mpa.pr_update_dur *= 2
            mpa.pr_update_ts = update_time + timedelta(hours=mpa.pr_update_dur)
            db.session.commit()
            print('OK')
        except Exception as e:
            error_dict[p.id] = str(e)
            print(f'{p.id} - {e}')
        print('----------------')

msg = ''
if sent_own or sent_kb or ult_err or neg_margin or no_result:
    if sent_own:
        msg += 'Zu folgenden Produkt-IDs wurde der eigene Preis übertragen:<br>\n'
        i=0
        while i*25<len(sent_own):
            msg += ','.join(sent_own[i*25:(i+1)*25]) + '<br>\n'
            i+=1
    if (sent_own and sent_kb) or (sent_own and neg_margin) or (sent_own and ult_err) or (sent_own and no_result):
        msg += '<br>-----------------------<br><br>\n'
    if sent_kb:
        msg += 'Zu folgenden Produkt-IDs wurde der Kuchenboden übertragen:<br>\n'
        i=0
        while i*25<len(sent_kb):
            msg += ','.join(sent_kb[i*25:(i+1)*25]) + '<br>\n'
            i+=1
    if (sent_kb and neg_margin) or (sent_kb and ult_err) or (sent_kb and no_result):
        msg += '<br>-----------------------<br><br>\n'
    if neg_margin:
        msg += 'Zu folgenden Produkt-IDs wurde ein Preis mit negativer Marge übertragen:<br>\n'
        i=0
        while i*25<len(neg_margin):
            msg += ','.join(neg_margin[i*25:(i+1)*25]) + '<br>\n'
            i+=1
    if (neg_margin and ult_err) or (neg_margin and no_result):
        msg += '<br>-----------------------<br><br>\n'
    if ult_err:
        msg += 'Zu folgenden Produkt-IDs konnte kein Preis generiert werden:<br>\n'
        i=0
        while i*25<len(ult_err):
            msg += ','.join(ult_err[i*25:(i+1)*25]) + '<br>\n'
            i+=1
    if ult_err and no_result:
        msg += '<br>-----------------------<br><br>\n'
    if no_result:
        msg += 'Zu folgenden Produkt-IDs konnten keine Konkurrenz-Daten gefunden werden, während eine Marktpreis-Strategie aktiv ist:<br>\n'
        i=0
        while i*25<len(ult_err):
            msg += ','.join(no_result[i*25:(i+1)*25]) + '<br>\n'
            i+=1
    send_email('Idealo-Preis-Automatisierung', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)
