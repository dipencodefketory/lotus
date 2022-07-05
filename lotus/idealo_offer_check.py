# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Marketplace, Product, Marketplace_Product_Attributes, Stock, Product_Stock_Attributes, ProductTag, PrTagRelation, MPReport
import idealo_business
import idealo_offer
import time as t
from datetime import datetime
import pandas as pd
from zipfile import ZipFile
from io import BytesIO


auth = idealo_business.get_access_token()
gen_res = idealo_business.generate_offer_report(auth)
print(gen_res.text)
rep_id = gen_res.json()['id']
# rep_id = '9943624d-a46c-460c-ba10-d2cab4a3b460'
print(rep_id)
s = idealo_business.get_offer_report(auth, rep_id)
print(s.text)
status = s.json()['status']
while status == 'PROCESSING':
    print('PROCESSING')
    print('Wait 60 seconds.')
    print('---------------------------')
    s = idealo_business.get_offer_report(auth, rep_id)
    status = s.json()['status']
    t.sleep(60)
if status == 'SUCCESSFUL':
    print('SUCCESSFUL!')
    print('---------------------------')
    s = idealo_business.download_offer_report(auth, rep_id)
    idealo = Marketplace.query.filter_by(name='Idealo').first()
    query = db.session.query(
        Product, Marketplace_Product_Attributes
    ).filter(
        Product.id == Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == idealo.id
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).order_by(
        Product.id.desc()
    ).all()
    p_skus = [p.internal_id for p, _ in query]
    rec_failed_tag = ProductTag.query.filter_by(name='RECOGNITION FAILED', marketplace_id=idealo.id).first()
    dev_del_time_tag = ProductTag.query.filter_by(name='DEVIANT DELIVERY TIME', marketplace_id=idealo.id).first()
    legal_req_tag = ProductTag.query.filter_by(name='LEGAL REQUIREMENTS', marketplace_id=idealo.id).first()
    checkout_tag = ProductTag.query.filter_by(name='CHECKOUT', marketplace_id=idealo.id).first()
    active = 0
    active_short_sell = 0
    active_pre_order = 0
    inactive = 0
    uploaded = 0
    total_offers = 0
    pos_quant = 0
    oos_quant = 0   # OUT_OF_STOCK
    extra_skus = []
    not_found_skus = []
    i=0
    with ZipFile(BytesIO(s.content)) as z:
        for filename in z.namelist():
            df = pd.read_csv(z.open(filename))
            df.rename(columns={'PriceComparison/Checkout': 'PriceComp_Checkout'}, inplace=True)
            uploaded = int(df['Status'].count())
            active = int(df['Status'][(df['Status'] == 'online') & (df['PriceComp_Checkout'] == 'checkout')].count())
            inactive = int(df['Status'][(df['Status'] == 'online') & (df['PriceComp_Checkout'] == 'price comparison')].count())
            inactive += int(df['Status'][df['Status'] == 'offline'].count())
            print(f'Online: {active}')
            print(f'Offline: {inactive}')

            auth_dt = datetime.now()
            auth = idealo_offer.get_access_token()
            for row in df.itertuples():
                print(i)
                if (datetime.now()-auth_dt).seconds > 1800:
                    auth_dt=datetime.now()
                    auth = idealo_offer.get_access_token()
                i+=1
                total_offers += 1
                sku = str(row.SKU)
                if sku in p_skus:
                    p_skus.remove(sku)
                else:
                    extra_skus.append(sku)
                q = db.session.query(
                    Product, Marketplace_Product_Attributes
                ).filter(
                    Product.internal_id==sku
                ).filter(
                    Marketplace_Product_Attributes.product_id==Product.id
                ).filter(
                    Marketplace_Product_Attributes.marketplace_id==idealo.id
                ).first()
                if q is None:
                    not_found_skus.append(sku)
                    print('----------------------')
                    print(f'SKU NOT FOUND: {sku}.')
                    print('----------------------')
                    continue
                p, mpa = q
                rec_fail_conn = PrTagRelation.query.filter_by(product_id=p.id, tag_id=rec_failed_tag.id).first()
                dev_del_time_conn = PrTagRelation.query.filter_by(product_id=p.id, tag_id=dev_del_time_tag.id).first()
                legal_req_conn = PrTagRelation.query.filter_by(product_id=p.id, tag_id=legal_req_tag.id).first()
                checkout_conn = PrTagRelation.query.filter_by(product_id=p.id, tag_id=checkout_tag.id).first()
                if row.OfflineReason == 'product recognition failed' and rec_fail_conn is None:
                    db.session.add(PrTagRelation(p.id, rec_failed_tag.id))
                elif row.OfflineReason != 'product recognition failed' and rec_fail_conn is not None:
                    db.session.delete(rec_fail_conn)
                if row.OfflineReason == 'deviant delivery time' and dev_del_time_conn is None:
                    db.session.add(PrTagRelation(p.id, dev_del_time_tag.id))
                elif row.OfflineReason != 'deviant delivery time' and dev_del_time_conn is not None:
                    db.session.delete(dev_del_time_conn)
                if row.OfflineReason == 'legal requirements' and legal_req_conn is None:
                    db.session.add(PrTagRelation(p.id, legal_req_tag.id))
                elif row.OfflineReason != 'legal requirements' and legal_req_conn is not None:
                    db.session.delete(legal_req_conn)
                if row.PriceComp_Checkout=='checkout' and checkout_conn is None:
                    db.session.add(PrTagRelation(p.id, checkout_tag.id))
                elif row.PriceComp_Checkout!='checkout' and checkout_conn is not None:
                    db.session.delete(checkout_conn)
                db.session.commit()
                r = idealo_offer.get_offer(auth, p.internal_id)
                if r.ok:
                    data = r.json()
                    if int(data["quantityPerOrder"]) > 0 and row.PriceComp_Checkout == 'checkout' and row.Status == 'online':
                        pos_quant += 1
                        active_short_sell += int(p.short_sell is True)
                        active_pre_order += int(p.release_date > datetime.now()) if p.release_date else 0
                    else:
                        oos_quant += 1
                    if row.LinkToIdealo in ['', None] or row.LinkToIdealo!=row.LinkToIdealo:
                        p.mp_offer_check(marketplace_id=idealo.id, quant=int(data["quantityPerOrder"]), price=float(data["price"]), not_listed=True)
                    else:
                        p.mp_offer_check(marketplace_id=idealo.id, quant=int(data["quantityPerOrder"]), price=float(data["price"]), not_listed=False)
                else:
                    p.mp_offer_check(marketplace_id=idealo.id, quant=None, price=None, not_listed=True)

    if not_found_skus:
        print(f'Not found SKUS: {not_found_skus}')
    if extra_skus:
        print(f'Extra SKUS: {extra_skus}')
    if p_skus:
        print(f'Not in table: {p_skus}')

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
        Marketplace_Product_Attributes.marketplace_id == idealo.id
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).count()

    est_active_short_sell = db.session.query(
        Marketplace_Product_Attributes, Product
    ).join(
        psas, psas.c.product_id == Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == idealo.id
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
        psas, psas.c.product_id == Marketplace_Product_Attributes.product_id
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == idealo.id
    ).filter(
        Marketplace_Product_Attributes.product_id == Product.id
    ).filter(
        Product.release_date > datetime.now()
    ).filter(
        Marketplace_Product_Attributes.uploaded == True
    ).count()

    if active != pos_quant:
        print(f'Online: {active} - Pos-Quant: {pos_quant}')
    if inactive != oos_quant:
        print(f'Offline: {inactive} - OOS-Quant: {oos_quant}')

    db.session.add(MPReport(est_uploaded=est_uploaded, est_active=est_active, est_active_short_sell=est_active_short_sell, est_active_pre_order=est_active_pre_order, est_inactive=est_uploaded - est_active, uploaded=uploaded,
                            active=active, active_short_sell=active_short_sell, active_pre_order=active_pre_order, inactive=inactive, marketplace_id=idealo.id))
    db.session.commit()
