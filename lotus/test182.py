# -*- coding: utf-8 -*-

from lotus import db, env_vars_path
from basismodels import Product, PricingAction, PricingLog, Sale, Product_Stock_Attributes
import idealo_offer
import ebay_api

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv, set_key


load_dotenv(env_vars_path)

dt = datetime.now()
r = ebay_api.refresh_access_token(os.environ['EBAY_OAUTH_REFRESH_TOKEN'])
data = r.json()
os.environ['EBAY_OAUTH_TOKEN'] = data['access_token']
set_key(env_vars_path, 'EBAY_OAUTH_TOKEN', data['access_token'])

authorization = idealo_offer.get_access_token()

query = db.session.query(
    Product, Product_Stock_Attributes
).filter(
    Product.id == Product_Stock_Attributes.product_id
).filter(
    Product_Stock_Attributes.stock_id == 1
).filter(
    Product_Stock_Attributes.quantity > 0
).filter(
    Product.short_sell == True
).filter(
    Product.cheapest_stock_id == 6
).filter(
    Product.id >= 9287
).order_by(
    Product.id
).all()
le = len(query)

for i, (p, _) in enumerate(query):
    print(f'{i}/{le}\t\t{p.id}')
    if datetime.now() - timedelta(minutes=50) > dt:
        dt = datetime.now()
        authorization = idealo_offer.get_access_token()
        r = ebay_api.refresh_access_token(os.environ['EBAY_OAUTH_REFRESH_TOKEN'])
        data = r.json()
        os.environ['EBAY_OAUTH_TOKEN'] = data['access_token']
        set_key(env_vars_path, 'EBAY_OAUTH_TOKEN', data['access_token'])
    for mpa in p.marketplace_attributes:
        if mpa.uploaded:
            try:
                r = p.mp_prq_update(mpa.marketplace_id, shipping_time=True, authorization=authorization)
                if not r.ok:
                    print('----------------------------------------------------------------------------------------------------')
                    print(r.text)
                    print('----------------------------------------------------------------------------------------------------')
            except Exception as e:
                print('----------------------------------------------------------------------------------------------------')
                print(e)
                print('----------------------------------------------------------------------------------------------------')
