# -*- coding: utf-8 -*-

from lotus import db, env_vars_path
from basismodels import Marketplace_Product_Attributes
import idealo_offer

from datetime import datetime, timedelta
import logging
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv, set_key

#if os.environ['MPA_UPDATE_ACTIVE'] == '1':
#    raise SystemError('Blocked by active script.')
os.environ['MPA_UPDATE_ACTIVE'] = '1'
set_key(env_vars_path, 'MPA_UPDATE_ACTIVE', os.environ['MPA_UPDATE_ACTIVE'])

load_dotenv(env_vars_path)

logging.basicConfig(filename=os.path.abspath(os.environ.get('LOG_FILENAME')), level=logging.INFO)
dt = datetime.now()
idealo_access = idealo_offer.get_access_token()
ebay_access = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')

mpas = Marketplace_Product_Attributes.query.filter_by(update=True).limit(15).all()
print(mpas)
for mpa in mpas:
    if datetime.now() - timedelta(minutes=50) > dt:
        dt = datetime.now()
        authorization = idealo_offer.get_access_token()
    if mpa.uploaded is not True:
        mpa.update = False
        mpa.update_quantity = None
        mpa.update_price = None
        db.session.commit()
    else:
        quantity = True if mpa.update_quantity is not None else False
        price = True if mpa.update_price is not None else False
        try:
            if mpa.marketplace.name == 'Idealo':
                logging.log(msg='--------------------------------------------------------------------------------', level=20)
                logging.log(msg='IDEALO', level=20)
                logging.log(msg=f'{datetime.now()} - {mpa.product_id}', level=20)
                logging.log(msg=f'quantity={mpa.update_quantity}', level=20)
                logging.log(msg=f'price={mpa.update_price}', level=20)
                r = mpa.product.mp_prq_update(authorization=idealo_access, marketplace_id=mpa.marketplace_id, quantity=quantity, price=price, custom_price=mpa.update_price, custom_quantity=mpa.update_quantity)
                logging.log(msg=f'r.ok={r.ok}', level=20)
            elif mpa.marketplace.name == 'Ebay':
                logging.log(msg='--------------------------------------------------------------------------------', level=20)
                logging.log(msg='EBAY', level=20)
                logging.log(msg=f'{datetime.now()} - {mpa.product_id}', level=20)
                logging.log(msg=f'quantity={mpa.update_quantity}', level=20)
                logging.log(msg=f'price={mpa.update_price}', level=20)
                r = mpa.product.mp_prq_update(authorization=ebay_access, marketplace_id=mpa.marketplace_id, quantity=quantity, price=price, custom_price=mpa.update_price, custom_quantity=mpa.update_quantity)
                logging.log(msg=f'r.ok={r.ok}', level=20)
            else:
                logging.log(msg='--------------------------------------------------------------------------------', level=20)
                logging.log(msg=f'{datetime.now()} - {mpa.product_id}', level=20)
                logging.log(msg=f'MP-Update for Marketplace {mpa.marketplace.name} not implemented.', level=20)
                continue
            if r.ok:
                mpa.update_quantity = None
                mpa.update_price = None
                mpa.update = False
                db.session.commit()
            else:
                if mpa.marketplace.name == 'Idealo':
                    data = r.json()
                    if 'No offer found' in data['generalErrors'][0]:
                        if mpa.update_quantity == 0:
                            mpa.update_quantity = None
                            mpa.update_price = None
                            mpa.update = False
                            db.session.commit()
                        else:
                            logging.log(msg='UPLOAD', level=20)
                            r = mpa.product.mp_upload(authorization=idealo_access, marketplace_id=mpa.marketplace_id, custom_price=mpa.update_price, custom_quantity=mpa.update_quantity)
                            logging.log(msg=f'r.ok={r.ok}', level=20)
                            if r.ok:
                                mpa.update_quantity = None
                                mpa.update_price = None
                                mpa.update = False
                                db.session.commit()
                            else:
                                logging.log(msg='ERROR', level=20)
                                logging.log(msg=r.text, level=20)
                else:
                    mpa.update_quantity = None
                    mpa.update_price = None
                    mpa.update = False
                    db.session.commit()
                    logging.log(msg='ERROR', level=20)
                    logging.log(msg=r.text, level=20)
                logging.log(msg='--------------------------------------------------------------------------------', level=20)
        except Exception as e:
            mpa.update_quantity = None
            mpa.update_price = None
            mpa.update = False
            db.session.commit()
            logging.log(msg='--------------------------------------------------------------------------------', level=20)
            logging.exception(f'{datetime.now()} - {mpa.product_id}')
            logging.log(msg='--------------------------------------------------------------------------------', level=20)

os.environ['MPA_UPDATE_ACTIVE'] = '0'
set_key(env_vars_path, 'MPA_UPDATE_ACTIVE', os.environ['MPA_UPDATE_ACTIVE'])
