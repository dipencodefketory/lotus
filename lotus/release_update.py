# -*- coding: utf-8 -*-

from lotus import db, env_vars_path
from basismodels import Product, Marketplace_Product_Attributes, Marketplace, Marketplace_Product_Attributes_Description, Stock, PSAUpdateQueue
import idealo_offer
from functions import working_days_in_range

from datetime import datetime, date, timedelta
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv

load_dotenv(env_vars_path)

products = Product.query.filter(
    Product.release_date >= datetime.now().date()
).all()

ebay_tr_auth = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_PATH')), domain="api.ebay.com", siteid='77')
idealo_auth = idealo_offer.get_access_token()
idealo = Marketplace.query.filter_by(name='Idealo').first()
ebay = Marketplace.query.filter_by(name='Ebay').first()
count_idealo_updates = 0
count_ebay_updates = 0

for p in products:
    try:
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=2, product_id=p.id).first()
        if mpa.uploaded:
            w_days = working_days_in_range(date.today(), p.release_date.date()) if p.release_date >= datetime.now() else 0
            if p.cheapest_stock_id:
                stock = Stock.query.filter_by(id=p.cheapest_stock_id).first()
                lag_days = stock.lag_days
            else:
                lag_days = 5
            w_days += lag_days
            if w_days == 20:
                mpa.curr_stock = min(max(0, p.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else p.get_own_stock()), mpa.max_stock)
                mpa.update_quantity = mpa.curr_stock
                p.generate_mp_price(mpa.marketplace_id, 3, min_margin=.01, send=False, save=True)
                mpa.update_price = mpa.selling_price
                mpa.update = True
                mpa.pr_update_dur = 6
                k = datetime.now().hour // 6
                mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
                db.session.commit()
        elif mpa.upload_ready is True:
            w_days = working_days_in_range(date.today(), p.release_date.date()) if p.release_date >= datetime.now() else 0
            if p.cheapest_stock_id:
                stock = Stock.query.filter_by(id=p.cheapest_stock_id).first()
                lag_days = stock.lag_days
            else:
                lag_days = 5
            w_days += lag_days
            if w_days == 20:
                mpa.curr_stock = min(max(0, p.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else p.get_own_stock()), mpa.max_stock)
                mpa.update_quantity = mpa.curr_stock
                p.generate_mp_price(mpa.marketplace_id, 3, min_margin=.01, send=False, save=True)
                mpa.update_price = mpa.selling_price
                mpa.update = True
                mpa.pr_update_dur = 6
                k = datetime.now().hour // 6
                mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
                db.session.commit()
                p.mp_upload(2)
        for mpa in p.marketplace_attributes:
            if mpa.marketplace.name == 'Idealo':
                title = False
                if p.release_date.date() == datetime.now().date():
                    if ' - Release: ' in mpa.name:
                        title = True
                        mpa.name = ' - '.join(mpa.name.split(' - ')[:-1])
                    db.session.add(PSAUpdateQueue(p.id))
                    db.session.commit()
                if mpa.uploaded is True:
                    p.mp_update(idealo.id, title=title, shipping_time=True, authorization=idealo_auth)
                    count_idealo_updates += 1
            if mpa.marketplace.name == 'Ebay':
                description = False
                if p.release_date.date() == datetime.now().date():
                    description = True
                    dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                        marketplace_product_attributes_id=mpa.id
                    ).filter(
                        Marketplace_Product_Attributes_Description.text.like("%WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN%")
                    ).first()
                    dscrpt.text = dscrpt.text if 'Release-Datum: ' not in dscrpt.text else '\n'.join(dscrpt.text.split('\n')[:-1])
                    db.session.add(PSAUpdateQueue(p.id))
                    db.session.commit()
                if mpa.uploaded is True:
                    p.mp_update(ebay.id, shipping_time=True, description=description, description_revise_mode='Replace', authorization=ebay_tr_auth)
                    count_ebay_updates += 1
    except Exception as e:
        print(e)

print(f'IDEALO-UPDATES: {count_idealo_updates}')
print(f'EBAY-UPDATES: {count_ebay_updates}')