# -*- coding: utf-8 -*-

from lotus import env_vars_path, db
from basismodels import Product, Marketplace, Product_Stock_Attributes, PSAUpdateQueue, StockUpdateQueue
from routines import ab_product_update
import afterbuy_api
import idealo_offer

from sqlalchemy import or_
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ETree
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv, set_key


load_dotenv(env_vars_path)
logging.basicConfig(filename=os.path.abspath(os.environ.get('PSA_UPDATE_LOG_PATH')), level=logging.INFO)

#if os.environ['PSA_UPDATE_ACTIVE'] == '1':
#    raise SystemError('Blocked by active script.')
os.environ['PSA_UPDATE_ACTIVE'] = '1'
set_key(env_vars_path, 'PSA_UPDATE_ACTIVE', os.environ['PSA_UPDATE_ACTIVE'])

update_queue = db.session.query(PSAUpdateQueue.product_id).group_by(PSAUpdateQueue.product_id).limit(360).all()
p_ids = [el[0] for el in update_queue]

print(p_ids)

products = Product.query.filter(
    Product.id.in_(p_ids)
).order_by(
    Product.id
).all()

del_query = PSAUpdateQueue.query.filter(PSAUpdateQueue.product_id.in_(p_ids)).all()

for el in del_query:
    db.session.delete(el)
    db.session.commit()

dt = datetime.now()
request_quant = 250
ebay_tr_auth = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_PATH')), domain="api.ebay.com", siteid='77')
idealo_auth = idealo_offer.get_access_token()
idealo = Marketplace.query.filter_by(name='Idealo').first()
ebay = Marketplace.query.filter_by(name='Ebay').first()

i=0
while i * request_quant < len(products):
    if datetime.now() - timedelta(minutes=30) > dt:
        dt = datetime.now()
        idealo_auth = idealo_offer.get_access_token()
    afterbuy_ids = [product.internal_id for product in products[i * request_quant: (i+1) * request_quant]]
    product_ids = set([])
    r = afterbuy_api.get_shop_products({'ProductID': afterbuy_ids})
    tree = ETree.fromstring(r.text)
    p_tree = [item for item in tree.iter() if item.tag == 'Product']
    stock_update = {}
    tag_dict = {}
    for p in p_tree:
        logging.log(msg='--------------------------------------------------------------------------------', level=20)
        try:
            afterbuy_id = p.find('ProductID').text
            logging.log(msg=afterbuy_id, level=20)
            auction_quant = p.find('AuctionQuantity').text
            quant = p.find('Quantity').text
            product = Product.query.filter_by(internal_id=afterbuy_id).first()
            if product:
                short_sell_off, no_stock, short_sell_on, back_in_stock, mp_update_dict, tags = product.psa_update()
                logging.log(msg=datetime.now(), level=20)
                logging.log(msg=product.id, level=20)
                logging.log(msg=f'{int(short_sell_off) * "SHORT_SELL_OFF"}{int(no_stock) * "NO_STOCK"}{int(short_sell_on) * "SHORT_SELL_ON"}{int(back_in_stock) * "BACK_IN_STOCK"}', level=20)
                logging.log(msg=mp_update_dict, level=20)
                if tags:
                    logging.log(msg=tags, level=20)
                update_quantity = False
                update_price = False
                psa = Product_Stock_Attributes.query.filter_by(product_id=product.id, stock_id=1).first()
                if tags:
                    tag_dict[product.id] = tags
                if short_sell_off is True or no_stock is True or short_sell_on is True or back_in_stock is True:
                    qu = None
                    if short_sell_off is True:
                        stock_update[product.id] = {'add_quantity': 100, 'add_auction_quantity': -100, 'merge_stock': 0}
                        db.session.add(StockUpdateQueue(-100, psa.id, psa.quantity))
                        db.session.commit()
                        qu = psa.quantity - 100
                    elif short_sell_on is True:
                        stock_update[product.id] = {'add_quantity': - 100, 'add_auction_quantity': 100, 'merge_stock': 0}
                        db.session.add(StockUpdateQueue(100, psa.id, psa.quantity))
                        db.session.commit()
                        qu = psa.quantity + 100
                    for mpa in product.marketplace_attributes:
                        if qu is not None:
                            mpa.curr_stock = min(max(0, qu - mpa.quantity_delta if mpa.quantity_delta else qu), mpa.max_stock)
                        else:
                            mpa.curr_stock = min(max(0, psa.quantity - mpa.quantity_delta if mpa.quantity_delta else psa.quantity), mpa.max_stock)
                        if mpa.uploaded:
                            update_quantity = True
                            if mpa.curr_stock > 0:
                                update_price = True
                        db.session.commit()
                    product_ids.add(product.id)
                for mpa in product.marketplace_attributes:
                    if mpa.uploaded is True:
                        if mpa.marketplace.name == 'Idealo' and mp_update_dict[mpa.marketplace_id]['update'] is True:
                            try:
                                r = product.mp_prq_update(idealo.id, price=update_price, quantity=update_quantity, custom_price=mp_update_dict[mpa.marketplace_id]['custom_price'], custom_quantity=mpa.curr_stock,
                                                          shipping_time=True, authorization=idealo_auth, pricingstrategy_id=mp_update_dict[mpa.marketplace_id]['ps_id'])
                                logging.log(msg=f'Response: {r.text}', level=20)
                                if not r.ok:
                                    data = r.json()
                                    if 'No offer found' in data['generalErrors'][0]:
                                        logging.log(msg='UPLOAD', level=20)
                                        r = mpa.product.mp_upload(authorization=idealo_auth, marketplace_id=mpa.marketplace_id,
                                                                  custom_price=mpa.selling_price if mp_update_dict[mpa.marketplace_id]['custom_price'] is None else mp_update_dict[mpa.marketplace_id]['custom_price'],
                                                                  custom_quantity=mpa.curr_stock)
                                        logging.log(msg=f'r.ok={r.ok}', level=20)
                                        if not r.ok:
                                            logging.log(msg='ERROR', level=20)
                                            logging.log(msg=r.text, level=20)
                            except Exception as e:
                                logging.log(msg=f'EXCEPTION: {str(e)}', level=20)
                        elif mpa.marketplace.name == 'Ebay' and mp_update_dict[mpa.marketplace_id]['update'] is True:
                            try:
                                r = product.mp_prq_update(ebay.id, price=update_price, quantity=update_quantity, custom_price=mp_update_dict[mpa.marketplace_id]['custom_price'], custom_quantity=mpa.curr_stock,
                                                          shipping_time=True, authorization=ebay_tr_auth, pricingstrategy_id=mp_update_dict[mpa.marketplace_id]['ps_id'])
                                logging.log(msg=f'Response: {r.text}', level=20)
                            except Exception as e:
                                logging.log(msg=f'EXCEPTION: {str(e)}', level=20)
                    elif mpa.marketplace.name == 'Idealo':
                        logging.log(msg='UPLOAD', level=20)
                        r = mpa.product.mp_upload(authorization=idealo_auth, marketplace_id=mpa.marketplace_id,
                                                  custom_price=mpa.selling_price if mp_update_dict[mpa.marketplace_id]['custom_price'] is None else mp_update_dict[mpa.marketplace_id]['custom_price'],
                                                  custom_quantity=mpa.curr_stock)
                        logging.log(msg=f'r.ok={r.ok}', level=20)
                        if not r.ok:
                            logging.log(msg='ERROR', level=20)
                            logging.log(msg=r.text, level=20)
                db.session.commit()
            else:
                logging.log(msg=f'NOT FOUND: {afterbuy_id}', level=20)
        except Exception as e:
            print(e)
            logging.log(msg=f'EXCEPTION: {str(e)}', level=20)
    ab_product_update(product_ids=list(product_ids), stock_update=stock_update)
    i+=1

os.environ['PSA_UPDATE_ACTIVE'] = '0'
set_key(env_vars_path, 'PSA_UPDATE_ACTIVE', '0')
