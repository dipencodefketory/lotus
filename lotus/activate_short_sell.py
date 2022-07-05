# -*- coding: utf-8 -*-

from lotus import env_vars_path, db
from basismodels import Product, Stock, Marketplace, Marketplace_Product_Attributes, Marketplace_Product_Attributes_Description
from functions import working_days_in_range
from routines import ab_product_update
import afterbuy_api
import idealo_offer

from datetime import datetime, timedelta, date
import xml.etree.ElementTree as ETree
from ebaysdk.finding import Connection as Finding_Connection
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv

load_dotenv(env_vars_path)

products = Product.query.filter(Product.id!=635).filter(Product.id>=1).order_by(Product.id).all()
request_quant = 250
ebay_fi_auth = Finding_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_ROOT')), siteid="EBAY-DE")
ebay_tr_auth = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_ROOT')), domain="api.ebay.com", siteid='77')
idealo_auth = idealo_offer.get_access_token()
possible_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]
stocks = Stock.query.filter(Stock.owned==False).all()
idealo = Marketplace.query.filter_by(name='Idealo').first()
ebay = Marketplace.query.filter_by(name='Ebay').first()

i=0
while i * request_quant < len(products):
    afterbuy_ids = [product.internal_id for product in products[i * request_quant: (i+1) * request_quant]]
    product_ids = []
    r = afterbuy_api.get_shop_products({'ProductID': afterbuy_ids})
    tree = ETree.fromstring(r.text)
    p_tree = [item for item in tree.iter() if item.tag == 'Product']
    stock_update = {}
    tag_dict = {}
    for p in p_tree:
        try:
            afterbuy_id = p.find('ProductID').text
            auction_quant = p.find('AuctionQuantity').text
            quant = p.find('Quantity').text
            product = Product.query.filter_by(internal_id=afterbuy_id).first()
            if product:
                print(product.id)
                if product.cheapest_stock_id:
                    curr_lag_days = Stock.query.filter_by(id=product.cheapest_stock_id).first().lag_days
                else:
                    curr_lag_days = -1
                stock, buying_price = product.get_cheapest_buying_price_all()
                product.cheapest_stock_id = stock.id if stock else None
                product.cheapest_buying_price = buying_price
                db.session.commit()
                mul = int(product.get_own_real_stock()<1)
                if product.release_date:
                    pre_order = True if product.release_date > datetime.now() else False
                else:
                    pre_order = False
                if buying_price is None:
                    if product.short_sell is True:
                        product.short_sell = False
                        stock_update[product.id] = {'quantity': 0, 'auction_quantity': int(auction_quant) + int(quant), 'merge_stock': 0}
                        tags = ['x']
                        if pre_order:
                            tags.append('PRE ORDER')
                        tag_dict[product.id] = tags
                        product_ids.append(product.id)
                        db.session.commit()
                        for mpa in product.marketplace_attributes:
                            if mpa.curr_stock > 0:
                                mpa.curr_stock = 0
                                if mpa.uploaded:
                                    mpa.update_quantity = 0
                                    mpa.update = True
                                db.session.commit()
                else:
                    update_shipping = False
                    us_ext = False
                    if product.release_date:
                        update_shipping = True
                        if product.release_date >= datetime.now():
                            us_ext = True
                    elif mul == 0:
                        product.release_date = datetime.now()-timedelta(days=1)
                        update_shipping = True
                    db.session.commit()
                    mpas = Marketplace_Product_Attributes.query.filter_by(product_id=product.id).all()
                    for mpa in mpas:
                        margin = .01 if product.short_sell or product.get_own_stock() > 5 else 0.15
                        if mpa.block_selling_price is not True:
                            r = product.generate_mp_price(mpa.marketplace_id, 3, min_margin=margin, send=False, save=True)
                        mpa.name = product.name if not mpa.name else mpa.name
                        if update_shipping:
                            w_days = working_days_in_range(date.today(), product.release_date.date()) + stock.lag_days * mul if us_ext else stock.lag_days * mul
                            if us_ext:
                                if mpa.marketplace.name == 'Idealo':
                                    mpa_name = mpa.name if ' - Release: ' not in mpa.name else ' - '.join(mpa.name.split(' - ')[:-1])
                                    mpa_name += f' - Release: {datetime.strftime(product.release_date, "%d.%m.%Y")}' if product.release_date > datetime.now() else ''
                                    mpa.name = mpa_name
                                    if us_ext or curr_lag_days != stock.lag_days:
                                        shipping_time = True
                                    product.mp_update(mpa.marketplace_id, title=True, price=True, brand=True, ean=True, mpn=True, shipping_time=shipping_time, authorization=idealo_auth)
                                elif mpa.marketplace.name == 'Ebay' and mpa.uploaded:
                                    dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                                        marketplace_product_attributes_id=mpa.id
                                    ).filter(
                                        Marketplace_Product_Attributes_Description.text.like("%WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN%")
                                    ).first()
                                    if dscrpt:
                                        dscrpt_text = dscrpt.text if 'Release-Datum: ' not in dscrpt.text else '\n'.join(dscrpt.text.split('\n')[:-1])
                                        if product.release_date > datetime.now():
                                            dscrpt_text += f'\nRelease-Datum: {datetime.strftime(product.release_date, "%d.%m.%Y")} / Voraussichtlicher Versand am {datetime.strftime(product.release_date - timedelta(days=1), "%d.%m.%Y")}'
                                        dscrpt.text = dscrpt_text
                                    if us_ext or curr_lag_days != stock.lag_days:
                                        if not mpa.marketplace_system_id:
                                            mpa.marketplace_system_id = product.get_ebay_id()
                                        if mpa.marketplace_system_id:
                                            product.mp_update(mpa.marketplace_id, shipping_time=True, description=True, description_revise_mode='Replace', authorization=ebay_tr_auth)
                        db.session.commit()
                    if stock.owned is True and product.short_sell is True:
                        product.short_sell = False
                        db.session.commit()
                        stock_update[product.id] = {'quantity': 0, 'auction_quantity': int(auction_quant)+int(quant), 'merge_stock': 0}
                        tags = ['x']
                        if pre_order:
                            tags.append('PRE ORDER')
                        tag_dict[product.id] = tags
                        product_ids.append(product.id)
                        for mpa in product.marketplace_attributes:
                            mpa.curr_stock = min(max(0, int(auction_quant)+int(quant) - mpa.quantity_delta if mpa.quantity_delta else int(auction_quant)+int(quant)), mpa.max_stock)
                            if mpa.uploaded:
                                mpa.update_quantity = mpa.curr_stock
                                mpa.update_price = mpa.selling_price
                                mpa.update = True
                                mpa.pr_update_dur = 6
                                mpa.pr_update_ts = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
                            db.session.commit()
                    elif stock.owned is False and product.short_sell is False:
                        product.short_sell = True
                        db.session.commit()
                        stock_update[product.id] = {'quantity': int(quant)-100, 'auction_quantity': int(auction_quant)+100, 'merge_stock': 0}
                        tags = ['LVK']
                        if pre_order:
                            tags.append('PRE ORDER')
                        tag_dict[product.id] = tags
                        product_ids.append(product.id)
                        for mpa in product.marketplace_attributes:
                            mpa.curr_stock = min(max(0, int(auction_quant)+100 - mpa.quantity_delta if mpa.quantity_delta else int(auction_quant)+100), mpa.max_stock)
                            if mpa.uploaded:
                                mpa.update_quantity = mpa.curr_stock
                                mpa.update_price = mpa.selling_price
                                mpa.update = True
                                mpa.pr_update_dur = 6
                                mpa.pr_update_ts = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
                            db.session.commit()
            else:
                print(f'NOT FOUND: {afterbuy_id}')
        except Exception as e:
            print(e)
    ab_product_update(product_ids=product_ids, stock_update=stock_update, tags=tag_dict)
    i+=1
