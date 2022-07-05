# -*- coding: utf-8 -*-

from lotus import env_vars_path
from basismodels import Product, Marketplace
import idealo_offer

from datetime import datetime
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv

load_dotenv(env_vars_path)

products = Product.query.filter(
    Product.release_date >= datetime.now()
).all()

ebay_tr_auth = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_ROOT')), domain="api.ebay.com", siteid='77')
idealo_auth = idealo_offer.get_access_token()
idealo = Marketplace.query.filter_by(name='Idealo').first()
ebay = Marketplace.query.filter_by(name='Ebay').first()

for p in products:
    try:
        p.mp_update(idealo.id, title=True, price=True, ean=True, shipping_time=True, authorization=idealo_auth)
        p.mp_update(ebay.id, shipping_time=True, description=True, description_revise_mode='Replace', authorization=ebay_tr_auth)
    except Exception as e:
        print(e)
